# 自定义用户认证的后端：实现多账号登录
from django.contrib.auth.backends import ModelBackend
import re
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings
from itsdangerous import BadData

from users.models import User
from . import constants


def check_verify_email_token(token):
    """反序列化token，获取user"""
    s = Serializer(settings.SECRET_KEY, constants.VERIFY_EMAIL_TOKEN_EXPIRES)
    try:
        data = s.loads(token)
    except BadData:
        return None
    else:
        # 从data中取出user_id和email
        user_id = data.get('user_id')
        email = data.get('email')
        try:
            user = User.objects.get(id=user_id,email=email)
        except User.DoesNotExist:
            return None
        else:
            return user

def generate_verify_email_url(user):
    """商城邮箱激活链接
        user:当前登录用户
        return:token
    """
    s = Serializer(settings.SECRET_KEY, constants.VERIFY_EMAIL_TOKEN_EXPIRES)
    data = {'user_id': user.id, 'email': user.email}
    token = s.dumps(data)  # 序列化对象
    return settings.EMAIL_VERIFY_URL + '?token=' + token.decode()


def get_user_by_account(account):
    """
    通过账号获取用户
    :param account: 用户名或手机号
    :return: user
    """
    # 效验username参数是用户名还是手机号
    try:
        if re.match(r'^1[3-9]\d{9}$', account):
            # username == 手机号
            user = User.objects.get(mobile=account)
        else:
            # username == 用户名
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user

class UsernameMobileBackend(ModelBackend):
    """自定义用户后端认证"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        重写认证方法
        :param request:
        :param username:用户名或手机号
        :param password: 密码明文
        :param kwargs: 额外参数
        :return: user
        """
        # 查询账户
        user = get_user_by_account(username)

        # 如果可以查询到用户，好需要的校验码是否正确
        if user and user.check_password(password):
            return user
        else:
            return None