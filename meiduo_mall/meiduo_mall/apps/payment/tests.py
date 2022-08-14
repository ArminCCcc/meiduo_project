from django.test import TestCase
import os
# Create your tests here.

app_private_key_string = open("keys/app_private_key.pem").read()  # 在pri文件下加入私钥
alipay_public_key_string = open("keys/alipay_public_key.pem").read()


if __name__ == '__main__':
    path = os.getcwd() + '11/meiduo_mall/apps/payment/keys/'
    print(path)
    # print(app_private_key_string)