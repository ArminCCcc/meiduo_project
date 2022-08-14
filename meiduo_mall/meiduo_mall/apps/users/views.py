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

from carts.utils import merge_carts_cookies_redis
from meiduo_mall.utils.views import LoginRequiredJSONMixin
from meiduo_mall.utils.response_code import RETCODE
from users.models import User,Address
from celery_tasks.email.tasks import send_verify_email
from users.utils import generate_verify_email_url,check_verify_email_token
from goods.models import SKU
from . import constants

# Create your views here.

# 创建日志输出器
longger = logging.getLogger('django')


class UserBrowseHistory(LoginRequiredJSONMixin,View):
    """用户浏览记录"""
    def post(self,request):
        # 保存用户商品浏览记录
        # 接收参数
        json_str = request.body.decode()  # json传过来的一个byte的json数据，将其转成字符串
        json_dict = json.loads(json_str)
        sku_id = json_dict.get('sku_id')
        #  效验参数
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('参数sku_id错误')

        # 保存sku_id到redis
        user = request.user
        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()
        # 先去重
        pl.lrem('history_%s' % user.id, 0, sku_id)    # 0代表全部截取
        # 在保存:最近浏览的商品在最前面
        pl.lpush('history_%s' % user.id, sku_id)
        # 最后截取
        pl.ltrim('history_%s' % user.id, 0, 4)
        pl.execute()

        # 响应结果
        return http.JsonResponse({'code':RETCODE.OK,'essmsg':'OK'})

    def get(self,request):
        """查询用户的浏览记录"""
        # 获取用户信息
        user = request.user
        # 创建redis对象
        redis_conn = get_redis_connection('history')
        # 取出列表数据（核心代码）
        sku_ids = redis_conn.lrange('history_%s' % user.id,0,-1)

        # 将模型转成字典
        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus.append({
                'id':sku.id,
                'name':sku.name,
                'price':sku.price,
                'default_image_url':sku.default_image.url
            })

        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'OK','skus':skus})


class UpdateTitleAddressView(LoginRequiredJSONMixin,View):
    """修改当前用户地址title"""
    def put(self,request,address_id):
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        if not title:
            return http.HttpResponseForbidden('缺少必要参数')

        try:
            address = Address.objects.get(id=address_id)
            # 将新标题覆盖旧标题
            address.title = title
            address.save()
        except Exception as e:
            longger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '更新标题失败'})

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '更新标题成功'})


class DefaultAddressView(LoginRequiredJSONMixin,View):
    """设置默认地址"""
    def put(self,request,address_id):
        """实现设置默认地址逻辑"""
        try:
            # 查询出当前哪个地址会作为登录用户的默认地址
            address = Address.objects.get(id=address_id)

            # 将指定的地址设置为当前登录用户的默认地址
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            longger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})


class UpdateDestoryAddressView(LoginRequiredJSONMixin,View):
    """更新和删除地址"""

    def put(self,request,address_id):
        """更新地址"""
        # 接收参数
        josn_str = request.body.decode()
        json_dict = json.loads(josn_str)
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        receiver = json_dict.get('receiver')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必要参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 使用最新地址信息覆盖指定旧的地址信息
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            longger.error(e)
            return http.JsonResponse({'code':RETCODE.DBERR,'errmsg':'修改地址失败'})

        # 响应新的地址信息给前端渲染
        try:
            address = Address.objects.get(id=address_id)
            # 构造新增地址字典数据
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }
        except Exception as e:
            longger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '修改地址失败'})

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '修改地址成功', 'address': address_dict})

    def delete(self,request,address_id):
        """删除地址"""
        # 实现指定地址的逻辑删除：is_deleted
        try:
            address = Address.objects.get(id=address_id)
            address.is_deleted = True
            address.save()
        except Exception as e:
            longger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '删除地址失败'})

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})

class AddressCreateView(LoginRequiredJSONMixin,View):
    """新增地址"""

    def post(self, request):

        # 判断用户地址数量是否超过上限：查询当前登录用户的地址数量
        # count = Address.objects.filter(user=request.user).count()
        count = request.user.addresses.count()  # 一对多，使用related_name查询
        if count > constants.USER_ADDRESS_COUNTS_LIMIT:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '超出用户地址上限'})
        # 接收参数
        josn_str = request.body.decode()
        json_dict = json.loads(josn_str)
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        receiver = json_dict.get('receiver')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver,province_id,city_id,district_id,place,mobile]):
            return  http.HttpResponseForbidden('缺少必要参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 保存用户传入的地址信息
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,# 标题默认就是收货人
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email,
            )

            # 如果登录用户没有默认地址，我们需要指定默认地址
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except Exception as e:
            longger.error(e)
            return http.JsonResponse({'code':RETCODE.DBERR,'errmsg':'新增地址失败'})

        # 构造新增地址字典数据
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应新增地址结果：需要将新增的地址返回给前端渲染
        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'新增地址成功','address': address_dict})

class AddressView(View):
    """查询展示收货地址"""
    def get(self,request):
        # 查询并展示用户地址信息

        # 获取当前登录用户的对象
        login_user = request.user
        # 使用当前登录用户和iS_delete=False作为条件查询地址数据
        addresses = Address.objects.filter(user=login_user,is_deleted=False)

        # 将用户地址模型列表转字典列表：应为JsonResponse和Vue.js不认识模型类型，只有Django和jinja2魔板模板认识
        address_list = []
        for address in addresses:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }
            address_list.append(address_dict)

        # 构造上下文
        context = {
            # 'default_address_id':login_user.default_address_id ,# 没有默认值为None
            'default_address_id':login_user.default_address_id or '0',# 没有默认值为 为None时设置为0
            'addresses':address_list
        }
        return render(request, 'user_center_site.html',context)

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

        # 用户登录成功合并cookie购物车到redis购物车
        response = merge_carts_cookies_redis(request=request,user=user,response=response)
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