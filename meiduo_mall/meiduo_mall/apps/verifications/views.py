from django.shortcuts import render
from django.views import View
from django_redis import  get_redis_connection
from django import http
from . import constants
import random,logging

from verifications.libs.captcha import fcaptcha
from meiduo_mall.utils.response_code import RETCODE
from verifications.libs.alibabacloud_sample.simple import CCP

# Create your views here.


# 创建日志输出器
logger = logging.getLogger('django')


class SMSCodeView(View):
    """短信验证码"""
    def get(self,request,mobile):

        # 接收参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('uuid')
        # 效验参数
        if not all ([mobile,image_code_client,uuid]):
            return http.HttpResponseForbidden('缺少必要参数')
        # 创建连接到redis的对象
        redis_conn = get_redis_connection('verify_code')

        # 判断用户是否频繁发送验证码
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        # 如果不为空则证明用户发送验证码间隔不超过60秒，return请求
        if send_flag:
            return http.JsonResponse({'code':RETCODE.THROTTLINGERR,'errmsg':'发送短信过于频繁'})

        # 提取图形验证码
        image_code_server = redis_conn.get('img_%s' % uuid)
        if image_code_server is None:
            return http.JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'图形验证码已失效'})
        # 删除图形验证码
        redis_conn.delete('img_%s' % uuid)
        # 对比图形验证码
        image_code_server = image_code_server.decode() # 将bytes转为字符串进行比较
        if image_code_client.lower() != image_code_server.lower(): # 转小写,在比较
            return http.JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'输入的图形验证码有误'})

        # 生成短信验证码 随机6位数字
        sms_code = '%06d' % random.randint(0,999999)
        logger.info(sms_code) # 手动输出日志，记录短信验证码

        # 创建pipline管道
        pl = redis_conn.pipeline()
        # 将命令添加到队列中
        #保存短信验证码
        pl.setex('sms_%s' % mobile,constants.SMS_CODE_REDIS_EXPIRES,sms_code)
        # 保存发送验证码的标记
        pl.setex('send_flag_%s' % mobile,constants.SEND_SMS_CODE_INTERVAL,1)
        # 执行
        pl.execute()

       # 发送短信验证码
        CCP().send_template_sms(mobile,sms_code)

        # 响应结果
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'发送短信成功'})



class ImageCodeView(View):
    """+  """
    def get(self, request, uuid):

        # 实现主体业务逻辑：生成，保存，响应图形验证码
        # 生成图形验证码
        text,image = fcaptcha.captcha.generate_captcha()

        # 保存图形验证码
        redis_conn = get_redis_connection('verify_code')
        # redis_conn.setex('key','expires','value')
        redis_conn.setex('img_%s' % uuid,constants.IMAGE_CODE_REDIS_EXPIRES,text)

        # 响应图形验证码
        return http.HttpResponse(image,content_type='image/jpg')




