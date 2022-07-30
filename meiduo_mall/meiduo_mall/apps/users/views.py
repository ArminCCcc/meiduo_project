from django import http
from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.views import View
import re
from django.db import DatabaseError
from django.urls import reverse
from django.contrib.auth import login
from meiduo_mall.utils.response_code import RETCODE
from users.models import User

# Create your views here.


class UsernameCountView(View):
    def get(self,request,username):
        # 接收和校验参数
        # 实现主体业务逻辑：使用username查询对应的记录的条数（filter返回的是结果集）
        count = User.objects.filter(username=username).count()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg':'OK','count':count})



class Registerview(View):
    """用户注册"""
    def get(self, request):
        """提供注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        """实现用户注册逻辑"""
        # 接收参数:表单参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')

        # 效验参数： 前后端的效验需要分开，避免恶意用户越过前端发请求，要保证后端的安全，前后端的效验逻辑相同
        # 判断参数是否齐全:all(列表)：回去校验列表中的元素是否为空，只要有一个为空，返回false
        if not all([username, password, password2, mobile, allow]):
            return http.HttpResponseForbidden('小伙子，别胡搞')
        # 判断用户名是否是5-20个字符
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        # 判断密码是否是8-20个字符
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        # 判断两次输入的密码是否一致
        if password != password2:
            return http.HttpResponseForbidden('两次输入的密码不一致!')
        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号')
        # 判断用户 是否勾选了协议
        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户协议')
        # 保存注册数据：是注册业务的核心
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
             return render(request, 'register.html', {'register_errmsg': '注册失败'})

        # 实现状态保持
        login(request,user)
        # 响应结果
        # return http.HttpResponse('finished,go to homepage')
        # reverse('content:index') == '/'
        return redirect(reverse('contents:index'))