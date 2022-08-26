from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token

urlpatterns = [
    # 登录路由
    url(r'^authorizations/$',obtain_jwt_token),
]