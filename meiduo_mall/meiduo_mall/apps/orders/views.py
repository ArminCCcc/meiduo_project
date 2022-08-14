from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from decimal import Decimal

from goods.models import SKU
from meiduo_mall.utils.views import LoginRequiredMixin
# Create your views here.
from users.models import Address


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
        #被勾选的商品数据
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
            'total_amount':total_count,
            'freight':freight,
            'payment_amount':total_amount + freight,
        }
        return render(request,'place_order.html',context)


