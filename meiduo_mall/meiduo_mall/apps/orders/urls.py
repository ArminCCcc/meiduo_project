from django.conf.urls import url

from orders.views import OrderSettlementView

urlpatterns = [
    # 结算订单
    url(r'^orders/settlement/$',OrderSettlementView.as_view(),name='settlement')
]