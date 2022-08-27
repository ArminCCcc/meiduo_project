from rest_framework import serializers
from goods.models import GoodsVisitCount

class UserGoodsSerializer(serializers.ModelSerializer):
    # 关联嵌套序列化返回字段指定
    category=serializers.StringRelatedField(read_only=True)

    class Meta:
        model = GoodsVisitCount
        fields = ('category','count')