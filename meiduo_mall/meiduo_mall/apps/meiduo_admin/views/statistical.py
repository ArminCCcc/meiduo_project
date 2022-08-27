from datetime import date, timedelta
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from goods.models import GoodsVisitCount
from meiduo_admin.serialziers.statistical import UserGoodsSerializer
from users.models import User


class UserCountView(APIView):
    """
    用户总量统计
    """
    # 权限指定
    permission_classes = [IsAdminUser]

    def get(self,request):
        # 1.获取当天日期
        now_date = date.today()
        # 2.获取用户总量
        count = User.objects.all().count()
        # 3.返回结果
        return Response({
            'date':now_date,
            'count':count
        })


class UserDayCountView(APIView):
    """
    用户当天新增数量统计
    """
    # 权限指定
    permission_classes = [IsAdminUser]

    def get(self,request):
        # 1.获取当天日期
        now_date = date.today()
        # 2.获取当天用户新增总量
        count = User.objects.filter(date_joined__gte=now_date).count()
        # 返回结果
        return Response({
            'date':now_date,
            'count':count
        })


class UserDayActiveCountView(APIView):
    """
    日活用户统计
    """
    # 权限指定
    permission_classes = [IsAdminUser]

    def get(self,request):
        # 1.获取当天日期
        now_date = date.today()
        # 2.获取当天用户活跃总量
        count = User.objects.filter(last_login__gte=now_date).count()
        # 返回结果
        return Response({
            'date':now_date,
            'count':count
        })


class UserDayOrdersCountView(APIView):
    """
    日下单用户数量
    """
    # 权限指定
    permission_classes = [IsAdminUser]

    def get(self,request):
        # 1.获取当天日期
        now_date = date.today()
        # 2.获取当天下单用户总量
        count = len(set(User.objects.filter(orders__create_time__gte=now_date)))
        # 返回结果
        return Response({
            'date':now_date,
            'count':count
        })


class UserMonthCountView(APIView):
    """
    月新增用户统计
    """
    # 权限指定
    permission_classes = [IsAdminUser]

    def get(self,request):
        # 1.获取当天日期
        now_date = date.today()
        # 获取一个月之前的日期
        begin_date = now_date - timedelta(days=29)
        data_list = []
        for i in range(30):
            # 起始日期
            index_date = begin_date  + timedelta(days=i)
            # 第二天的日期（起始日期的下一天）
            next_date  = begin_date + timedelta(days=i+1)
            count  = User.objects.filter(date_joined__gte=index_date,date_joined__lt=next_date).count()
            data_list.append({
                'count':count,
                'date':index_date
            })

        # 返回结果
        return Response(data_list)


class UserGoodsCountView(APIView):
    """
    日分类商品访问量统计
    """
    # 权限指定
    permission_classes = [IsAdminUser]

    def get(self,request):
        # 1.获取当天日期
        now_date = date.today()
        # 2.获取当天分类访问量
        goods = GoodsVisitCount.objects.filter(date__gte=now_date)
        # 生成序列化器返回data
        ser = UserGoodsSerializer(goods,many=True)
        # 返回结果
        return Response(ser.data)