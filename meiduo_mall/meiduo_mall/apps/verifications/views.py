from django.shortcuts import render
from django.views import View
from verifications.libs.captcha import fcaptcha
from django_redis import  get_redis_connection
from django import http
# Create your views here.

class ImageCodeView(View):
    """图形验证码"""
    def get(self, request, uuid):

        # 实现主体业务逻辑：生成，保存，响应图形验证码
        # 生成图形验证码
        text,image = fcaptcha.captcha.generate_captcha()

        # 保存图形验证码
        redis_conn = get_redis_connection('verify_code')
        # redis_conn.setex('key','expires','value')
        redis_conn.setex('img_%s' % uuid,120,text)

        # 响应图形验证码
        return http.HttpResponse(image,content_type='image/jpg')




