import re

from rest_framework import serializers

from users.models import User


class UserSerialzier(serializers.ModelSerializer):
    """
        用户序列化器
    """

    class Meta:
        model = User
        fields = ('id','username','mobile','email','password') # id字段默认readonly
        extra_kwargs={
            # 控制password参与 validate 只参与反序列化
            'password':{
                'write_only': True,
                'max_length': 20,
                'min_length': 8,
            },
            'username': {
                'max_length': 20,
                'min_length': 5,
            }



        }

    # 单一字段验证 validate+字段名 验证手机号
    def validate_mobile(self,value):
        if not re.match(r'1[3-9]\d{9}',value):
            raise serializers.ValidationError('手机格式不对')
        return value


    # 重写ModelSerializer create方法 对password进行加密
    def create(self, validated_data):
        # user = super().create(validated_data)
        # # 密码加密(django user类自带密码加密方法)
        # user.set_password(validated_data['password'])
        # user.save()

        # 第二种方法
        user = User.objects.create_user(**validated_data)
        return user