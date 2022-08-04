#!/usr/bin/env python
#coding=utf-8
import json

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcore.auth.credentials import AccessKeyCredential
from aliyunsdkcore.auth.credentials import StsTokenCredential
from aliyunsdkdysmsapi.request.v20170525.SendSmsRequest import SendSmsRequest

# credentials = AccessKeyCredential('LTAI5tGT91dKXwWYxyg3ZNZR', 'qb74xzOQUW3TJJLtG7XBi1xinGHPlk')
# # use STS Token
# # credentials = StsTokenCredential('<your-access-key-id>', '<your-access-key-secret>', '<your-sts-token>')
# client = AcsClient(region_id='cn-hangzhou', credential=credentials)

# request = SendSmsRequest()
# request.set_accept_format('json')
# request.set_PhoneNumbers('18309430701')
# request.set_SignName('阿里云短信测试')
# request.set_TemplateCode('SMS_154950909')
# request.set_TemplateParam('{"code":"123422"}')

# response = client.do_action_with_exception(request)
# python2:  print(response)
# print(str(response, encoding='utf-8'))

class CCP(object):
    """发送验证码的单例类"""


    # use STS Token
    # credentials = StsTokenCredential('<your-access-key-id>', '<your-access-key-secret>', '<your-sts-token>')


    def __new__(cls, *args, **kwargs):
        # 判断单例是否存在，_insance属性中存储的就是单例
        if not hasattr(cls,'_instance'):
            # 如果单例不存在,初始化单例
            cls._instance = super(CCP,cls).__new__(cls,*args,**kwargs)
            cls._instance.rest = SendSmsRequest()

            credentials = AccessKeyCredential('LTAI5tGT91dKXwWYxyg3ZNZR', 'qb74xzOQUW3TJJLtG7XBi1xinGHPlk')
            cls._instance.rest.client = AcsClient(region_id='cn-hangzhou', credential=credentials)
            cls._instance.rest.set_SignName('阿里云短信测试')
            cls._instance.rest.set_TemplateCode('SMS_154950909')
            # 返回单例
        return cls._instance

    def send_template_sms(self,phoneNumbers,sms_code):
        self._instance.rest.set_PhoneNumbers(phoneNumbers)
        self._instance.rest.set_TemplateParam({'code': sms_code})
        response = self._instance.rest.client.do_action_with_exception(self.rest)
        jsonResponse = json.loads(response)
        # print(jsonResponse)
        # print(str(response, encoding='utf-8'))
        if jsonResponse.get('Code') == 'OK':
            return 0
        else:
            return -1

if __name__ == '__main__':
    # CCP().send_template_sms('17710701940') # 18309430701 17710701940
    pass
    # json_info = "{'age': '12'}"
    # jstr_info_dump = json.dumps(json_info)
    # print(type(jstr_info_dump))
    # print('-'*8)
    # str = b'{"a":123,"b":"armin"}'
    # jstr = json.loads(str)
    # print(type(jstr))
    # print(jstr.get('b'))
    # # //print(str.get('a'))