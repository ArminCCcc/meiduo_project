from . import views
from django.conf.urls import url


urlpatterns = [
    # 首页广告
    url(r'^$', views.IndexView.as_view(), name='index'),

]