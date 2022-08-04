from django.conf.urls import url
from . import views

urlpatterns = [
     # 用户注册 : reverse(users:register) == '/register/'
     url(r'^register/$', views.Registerview.as_view(),name='register'),
     # 判断用户名是否重复
     url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view()),
     # 判断用户手机号是否重复
     url(r'^mobile/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
     # 用户登录
     url(r'^login/$',views.LoginView.as_view(),name='login'),
     # 用户退出登录


     url(r'^logout/$',views.LogoutView.as_view(),name='logout'),
     # 用户中心
     url((r'^info/$'), views.UserInfoView.as_view(),name='info'),
     # 添加邮箱
     url((r'^email/$'),views.EmailView.as_view()),
     # 验证邮箱
     url(r'^emails/verification/$', views.VerifyEmailView.as_view()),


]