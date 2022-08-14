from alipay import AliPay
from django import http
from django.conf import settings
from django.shortcuts import render
from django.views import View
import os

from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.utils.views import LoginRequiredJSONMixin
from payment.models import Payment


# Create your views here.
from orders.models import OrderInfo

class PaymentStatusView(LoginRequiredJSONMixin,View):
    """保存支付的订单状态"""

    def get(self,request):
        # 获取所有的查询字符串参数
        query_dict = request.GET
        # 将查询字符串参数的类型转成标准字典类型
        data = query_dict.dict()
        # 从字符串参数中提取出并移除sign
        signature = data.pop('sign')

        # 创建SDK对象
        # 创建支付宝支付对象
        path = os.getcwd() + '/meiduo_mall/apps/payment/keys/'
        app_private_key_string = open(path + 'app_private_key.pem').read()  # 在pri文件下加入私钥
        alipay_public_key_string = open(path + "alipay_public_key.pem").read()  # 在pub文件下加入支付宝公钥

        alipay = AliPay(  # (传入的公共参数，对任何接口都要传递)
            appid=settings.ALIPAY_APPID,  # 应用id
            app_notify_url=None,  # 默认回调url
            # 应用的公私钥
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # 加密标准
            debug=settings.ALIPAY_DEBUG  # 指定是否为开发环境
        )

        # 使用SDK对象，调用验证接口函数，得到验证结果
        success = alipay.verify(data,signature)

        # 如果验证通过，需要将支付宝的支付状态进行处理（将美多商城的订单ID和支付宝的订单ID把绑定）
        if success:
            # 美多商城维护的订单ID
            order_id = data.get('out_trade_no')
            # 支付宝维护的订单ID
            trade_id = data.get('trade_no')
            method = data.get('method')
            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_id
            )
            # 修改订单状态由待支付改为待评价
            OrderInfo.objects.filter(order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(
                status=OrderInfo.ORDER_STATUS_ENUM["UNCOMMENT"])

            context = {
                'trade_id':trade_id
            }
            return render(request,'pay_success.html',context)
        else:
            return http.HttpResponseForbidden('非法请求')


class PaymentView(LoginRequiredJSONMixin,View):
    """对接支付宝的支付接口"""
    def get(self,request,order_id):
        """
        :param reuest:
        :param order_id:当前要支付的订单ID
        :return:JSON
        """

        path = os.getcwd() + '/meiduo_mall/apps/payment/keys/'
        # 查询要支付的订单
        user = request.user
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user,
                                          status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('订单信息错误')

        app_private_key_string = open(path+'app_private_key.pem').read()  # 在pri文件下加入私钥
        alipay_public_key_string = open(path+"alipay_public_key.pem").read()  # 在pub文件下加入支付宝公钥

        # 创建支付宝支付对象
        alipay = AliPay(#(传入的公共参数，对任何接口都要传递)
            appid=settings.ALIPAY_APPID,# 应用id
            app_notify_url=None,  # 默认回调url
            #应用的公私钥
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2", # 加密标准
            debug=settings.ALIPAY_DEBUG # 指定是否为开发环境
        )

        # 生成登录支付宝连接
        # sdk对象对接支付宝的接口，得到登录页的地址
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="美多商城%s" % order_id,
            return_url=settings.ALIPAY_RETURN_URL,
        )

        # 响应登录支付宝连接
        # 真实环境电脑网站支付网关：https://openapi.alipay.com/gateway.do? + order_string
        # 沙箱环境电脑网站支付网关：https://openapi.alipaydev.com/gateway.do? + order_string
        alipay_url = settings.ALIPAY_URL + "?" + order_string
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'alipay_url': alipay_url})


