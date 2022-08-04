from django import http
from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.views import View
from django.db import DatabaseError
from django.urls import reverse
from django.contrib.auth import login,authenticate,logout
from django_redis import get_redis_connection
from django.contrib.auth.mixins import LoginRequiredMixin
import re,logging,json

from meiduo_mall.utils.views import LoginRequiredJSONMixin
from meiduo_mall.utils.response_code import RETCODE
from users.models import User
from celery_tasks.email.tasks import send_verify_email
from users.utils import generate_verify_email_url,check_verify_email_token
# Create your views here.

# 创建日志输出器
longger = logging.getLogger('django')


class VerifyEmailView(View):
    """验证邮箱"""
    def get(self, request):
        # 接收参数
        token = request.GET.get('token')
        # 效验参数
        if not token:
            return http.HttpResponseForbidden('缺少token')
        # 从token中提取用户信息user_id ==> user
        user = check_verify_email_token(token)
        if not user:
            return http.HttpResponseBadRequest('无效的token')
        # 将用户的email_active设置为True
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            longger.error(e)
            return http.HttpResponseServerError('激活邮箱失败')
        # 响应结果：重定向到用户中心
        return redirect(reverse('users:info'))


class EmailView(LoginRequiredJSONMixin,View):
    """添加邮箱"""
    def put(self, request):
        # 接收参数
        json_str = request.body.decode()  # body是byte类型
        json_dict = json.loads(json_str)
        email = json_dict.get('email')

        # 效验数据
        if not re.match(r'[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
            return http.HttpResponseForbidden('参数eamil有误')

        # 将用户传入的邮箱保存到用户数据库的email字段中
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            longger.error(e)
            return http.JsonResponse({'code':RETCODE.DBERR,'errmsg':'添加邮箱失败'})

        # 发送邮箱验证邮件
        verify_url = generate_verify_email_url(request.user)
        # 记得调用delay
        send_verify_email.delay(email,verify_url)

        # 响应结果
        return  http.JsonResponse({'code':RETCODE.OK,'errmsg':'OK'})


class UserInfoView(LoginRequiredMixin,View):
    """用户中心"""
    def get(self,request):
        """提供用户中心页面"""
        # if request.user.is_authenticated:
        #     return render(request,'user_center_info')
        # else:
        #     return redirect(reverse('user:login'))

        # 如果LoginRequiredMixin判断出用户已登录，request.user就是登录用户对象
        context = {
            'username':request.user.username,
            'mobile':request.user.mobile,
            'email':request.user.email,
            'email_active':request.user.email_active
        }

        return render(request,'user_center_info.html',context)

class LogoutView(View):
    """用户退出登录"""
    def get(self,request):
        """实现用户退出登录的逻辑"""
        # 清除状态保持信息
        logout(request)

        # 退出登录后重定向到首页
        response = redirect(reverse('contents:index'))
        # 删除cookie中的用户名
        response.delete_cookie('username')
        # 响应结果
        return response
class LoginView(View):
    """用户登录"""
    def get(self,request):
        """提供用户登录页面"""

        return render(request,'login.html')
        pass
    def post(self,request):
        """实现用户登录逻辑"""
        # 接收参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')
        # 校验参数
        if not all([username,password]):
            return http.HttpResponseForbidden('缺少必要参数')
        if not re.match(r'^[a-zA-z0-9_-]{5,20}$',username):
            return http.HttpResponseForbidden('请输入正确的用户名或手机号')
        if not re.match(r'^[0-9A-Za-z]{8,20}$',password):
            return http.HttpResponseForbidden('密码最少8位，最长20位')
        # 认证用户：使用账号查询用户是否存在，如果用户存在，再效验验证码是否正确
        user = authenticate(username=username,password=password)
        if user is None:
            return render(request,'login.html',{'account_errmsg': '账号或密码错误'})

        # 状态保持
        login(request,user)
        # 使用remembered确定保持状态的周期，(实现记住登录)
        if remembered != 'on':
        # 没有记住登录，状态保持在浏览器会话结束后就销毁
            request.session.set_expiry(0) # 单位是秒
        else:
            # 记住登录：状态保持周期为两周，默认是两周
            request.session.set_expiry(None)

        # 先取出next
        next = request.GET.get('next')
        if next:
            # 重定向到next
            response = redirect(next)
        else:
            # 重定向到首页
            # redirect就是一个response对象
            response = redirect(reverse('contents:index'))

        # 为了实现在首页右上角展示的用户信息，我们需要将用户名缓存到cookie中
        # response.set_cookie('key','val','expiry')
        response.set_cookie('username',user.username,max_age=3600 * 24 * 15 )

        # 响应结果：重定向到首页
        return response





class UsernameCountView(View):
    def get(self,request,username):
        # 接收和校验参数
        # 实现主体业务逻辑：使用username查询对应的记录的条数（filter返回的是结果集）
        count = User.objects.filter(username=username).count()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg':'OK','count':count})

class MobileCountView(View):
    def get(self,request,mobile):
        # 接收参数
        # 效验参数
        # 实现主题业务逻辑： 使用mobile查询对应的记录条数（filter返回的是结果集）
        count = User.objects.filter(mobile=mobile).count()

        return  http.JsonResponse({'code':RETCODE.OK,'errormsg':'OK','count':count})

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
        sms_code_client = request.POST.get('sms_code')

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
        # 判断验证码是否正确
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        if sms_code_server is None:
            return render(request,'register.html',{'sms_code_errmsg':'短信验证码已失效'})
        if sms_code_client != sms_code_server.decode():
            return render(request,'register',{'sms_code_errmsg':'输入的短信验证码有误'})
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

        # redirect就是一个response对象
        response = redirect(reverse('contents:index'))

        # 为了实现在首页右上角展示的用户信息，我们需要将用户名缓存到cookie中
        # response.set_cookie('key','val','expiry')
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)

        # 响应结果：重定向到首页
        return response