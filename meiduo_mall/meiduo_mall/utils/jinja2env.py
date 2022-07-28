from django.urls import reverse
from jinja2 import Environment
from django.contrib.staticfiles.storage import  staticfiles_storage


def jinja2_environment(**options):
    """jinja2环境"""
    # 创建环境对象
    env = Environment(**options)

    # 自定义语法
    env.globals.update({
        'static':staticfiles_storage.url,# 获取静态文件的前缀
        'url':reverse,# 反向解析 重定向
    })

    return env