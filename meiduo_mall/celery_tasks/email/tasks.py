from django.core.mail import send_mail
from django.conf import  settings
from  celery_tasks.main import celery_app
import logging

logger = logging.getLogger('django')
# bind:保证task对象会作为第一个参数自动传入
# name：异步任务别名
# retry_backoff：异步自动重试的时间间隔 第n次
# max_retries：异步自动重试的上限
@celery_app.task(bind=True,name='send_verify_email',retry_backoff=3)
def send_verify_email(self,to_email,verify_url):
    """定义发邮件的任务"""
    # send_mail('标题','普通邮件正文','发件人','收件人列表','富文本邮件正文（HTML）')

    subject = '美多商城邮箱验证'
    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用美多商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (to_email, verify_url, verify_url)
    try:
        send_mail(subject,'',settings.EMAIL_FROM,[to_email],html_message=html_message)
    except Exception as e:
        raise  self.retry(exec=e,max_retries=3)