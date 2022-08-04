import sys

from typing import List

from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


class Sample:
    def __init__(self):
        pass

    @staticmethod
    def create_client(
        access_key_id: str,
        access_key_secret: str,
    ) -> Dysmsapi20170525Client:
        """
        使用AK&SK初始化账号Client
        @param access_key_id:
        @param access_key_secret:
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config(
            # 您的 AccessKey ID,
            access_key_id='LTAI5tGT91dKXwWYxyg3ZNZR',
            # 您的 AccessKey Secret,
            access_key_secret='qb74xzOQUW3TJJLtG7XBi1xinGHPlk'
        )
        # 访问的域名
        config.endpoint = f'dysmsapi.aliyuncs.com'
        return Dysmsapi20170525Client(config)

    @staticmethod
    def main(
        args: List[str],
    ) -> None:
        client = Sample.create_client('accessKeyId', 'accessKeySecret')
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            sign_name='阿里云短信测试',
            template_code='SMS_154950909',
            phone_numbers='18309430701',
            template_param='{"code":"123422"}'
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
          response = client.send_sms_with_options(send_sms_request, runtime)
          print(response.body)
        except Exception as error:
            # 如有需要，请打印 error
            UtilClient.assert_as_string(error.message)

    @staticmethod
    async def main_async(
        args: List[str],
    ) -> None:
        client = Sample.create_client('accessKeyId', 'accessKeySecret')
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            sign_name='阿里云短信测试',
            template_code='SMS_154950909',
            phone_numbers='18309430701',
            template_param='{"code":"1234"}'
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            await client.send_sms_with_options_async(send_sms_request, runtime)
        except Exception as error:
            # 如有需要，请打印 error
            UtilClient.assert_as_string(error.message)


class CCP(object):
    """发送验证码的单例类"""
    def __new__(cls, *args, **kwargs):
        # 判断单例是否存在，_insance属性中存储的就是单例
        if not hasattr(cls,'_instance'):
            # 如果单例不存在,初始化单例
            cls._instance = super(CCP,cls).__new__(cls,*args,**kwargs)
            cls._instance.simple = Sample()
            client = cls._instance.simple.create_client('accessKeyId', 'accessKeySecret')
            client.send_sms_with_options(send_sms_request,runtime)
        # 返回单例
        return cls._instance


if __name__ == '__main__':
    Sample.main(sys.argv[1:])