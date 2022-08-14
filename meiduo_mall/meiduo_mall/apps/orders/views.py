import json

from django import http
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django_redis import get_redis_connection
from decimal import Decimal
from django.db import transaction

from goods.models import SKU
from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.utils.views import LoginRequiredMixin
# Create your views here.
from users.models import Address
from orders.models import OrderGoods,OrderInfo


class OrderSuccessView(LoginRequiredMixin,View):
    """提交订单成功页面"""
    def get(self,request):
        order_id = request.GET.get('order_id')
        payment_amount = request.GET.get('payment_amount')
        pay_method = request.GET.get('pay_method')

        context = {
            'order_id':order_id,
            'payment_amount':payment_amount,
            'pay_method':pay_method,
        }

        return render(request,'order_success.html',context)


class OrderCommitView(LoginRequiredMixin,View):
    """保存订单基本信息，订单商品信息"""
    # 接收信息
    def post(self,request):
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')

        # 效验参数
        if not all([address_id,pay_method]):
            return http.HttpResponseForbidden('缺少必要参数')
        try:
            address =Address.objects.get(id=address_id)
        except Address.DoesNotExit:
            return http.HttpResponseForbidden('参数address_id错误')
        # 判断pay_method是否合法
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'],OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return http.HttpResponseForbidden('参数pay_method错误')

        # 事务处理 开启一次事务
        with transaction.atomic():
            # 在数据库操作之前需要指定保存点，（回滚）
            save_id = transaction.savepoint()
            # 出现任何异常直接回滚
            try:
                # 获取登录用户
                user = request.user
                # 获取订单编号 时间+userid
                order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)
                # 保存订单基本信息
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal(0.00),
                    freight=Decimal(10.00),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY'] else OrderInfo.ORDER_STATUS_ENUM['UNSEND']
                )

                # 保存订单商品信息
                # 查询redis购物车被勾选的数据
                redis_conn = get_redis_connection('carts')
                # 所有的购物车数据
                redis_cart = redis_conn.hgetall('carts_%s' % user.id)
                # 被勾选的商品数据
                redis_selected = redis_conn.smembers('selected_%s' % user.id)
                # 构造购物车被勾选的数据
                new_cart_dict = {}
                for sku_id in redis_selected:
                    new_cart_dict[int(sku_id)] = int(redis_cart[sku_id])

                # 获取被勾选商品的sku_id
                sku_ids = new_cart_dict.keys()
                for sku_id in sku_ids:

                    # 每个商品都有多次下单机会，直到库存不足
                    while True:
                        # 判断商品数量是否大于库存，如果大于，响应库存不足
                        sku = SKU.objects.get(id=sku_id)# 查询商品和库存信息时，不能出现缓存，所以没有用filter

                        # 获取原始的库存和销量（加乐观锁）
                        origin_stock = sku.stock
                        origin_sales = sku.sales

                        # 获取要提及到的订单的商品数量
                        sku_count = new_cart_dict[sku_id]
                        # 判断商品数量是否大于库存，如果大于，响应库存不足
                        if sku_count > sku.stock:
                            # 库存不足时回滚
                            transaction.savepoint_rollback(save_id)
                            return http.JsonResponse({'code':RETCODE.STOCKERR,'errmsg':'库存不足'})

                        new_stock = origin_stock - sku_count
                        new_sales = origin_sales + sku_count
                        # 使用乐观锁更新数据.
                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,sales=new_sales)
                        # result返回值，如果更新数据时原始数据变化了，返回0表示有资源抢夺
                        if result == 0:
                            continue

                        # 减库存，加销量
                        # sku.stock -= sku_count
                        # sku.sales += sku_count
                        # sku.save()

                        # spu加销量
                        sku.spu.sales +=sku_count
                        sku.spu.save()

                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price,
                        )

                        # 累加订单商品的数量和总价到订单的基本信息表
                        order.total_count += sku_count
                        order.total_amount += sku_count * sku.price

                        # 下单成功break
                        break
                # 总订单费用加运费
                order.total_amount += order.freight
                order.save()
            except Exception as e:
                transaction.savepoint_rollback(save_id)
                return http.JsonResponse({'code':RETCODE.DBERR,'errmsg':'下单失败'})
            # 数据库操作成功，提交一次事务
            transaction.savepoint_commit(save_id)

        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'OK','order_id':order_id})


class OrderSettlementView(LoginRequiredMixin,View):
    """结算订单"""

    def get(self,request):
        # 查询并展示要结算的订单数据
        # 获取登录用户
        user = request.user
        # 查询用户的收货地址
        try:
            addresses = Address.objects.filter(user=user,is_deleted=False)
        except Exception as e:
            # 如果没有查询到收货地址可以直接编辑收货地址
            addresses = None
        # 查询购物车被勾选的数据
        redis_conn = get_redis_connection('carts')
        # 所有的购物车数据
        redis_cart = redis_conn.hgetall('carts_%s' % user.id)
        # 被勾选的商品数据
        redis_selected = redis_conn.smembers('selected_%s' %user.id)
        # 构造购物车被勾选的数据
        new_cart_dict = {}
        for sku_id in redis_selected:
            new_cart_dict[int(sku_id)] = int(redis_cart[sku_id])

        # 获取被勾选商品的sku_id
        sku_ids = new_cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        # 遍历skus给每个sku补充count数量和amount小计
        total_count = 0
        total_amount = Decimal(0.00)
        # 取出sku
        for sku in skus:
            sku.count = new_cart_dict[sku.id]
            sku.amount = sku.price * sku.count # Decimal类型数据

            total_count += sku.count
            total_amount += sku.amount # 类型不同不能计算。

        # 指定默认运费
        freight = Decimal(10.00)
        # 构造上下文

        context = {
            'addresses':addresses,
            'skus':skus,
            'total_count':total_count,
            'total_amount':total_amount,
            'freight':freight,
            'payment_amount':total_amount + freight,
        }
        return render(request,'place_order.html',context)


