from rest_framework.generics import ListCreateAPIView

from meiduo_admin.serialziers.users import UserSerialzier
from meiduo_admin.utils import PageNum
from users.models import User

# 继承ListCreateAPIView 同时拥有获取数据和保存数据的功能（post+get）相当于 ListAPIView + CreateAPIView
class UserView(ListCreateAPIView):
    """
        获取用户数据
    """
    # 指定查询集
    # 指定序列化器
    serializer_class = UserSerialzier
    # 使用分页器
    pagination_class = PageNum

    # 重写获取查询集数据的方法
    def get_queryset(self):
        if self.request.query_params == '':
            return User.objects.all()
        else:
            # request.query_params.get('keyword') 获取request url里的参数''keyword
            return User.objects.filter(username__contains=self.request.query_params.get('keyword'))
