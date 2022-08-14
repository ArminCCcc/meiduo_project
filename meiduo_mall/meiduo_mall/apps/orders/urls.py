from django.conf.urls import url

from orders.views import OrderSettlementView,OrderCommitView,OrderSuccessView

urlpatterns = [
    # 结算订单
    url(r'^orders/settlement/$',OrderSettlementView.as_view(),name='settlement'),
    # 提交订单
    url(r'^orders/commit/$',OrderCommitView.as_view()),
    url(r'^orders/success/$',OrderSuccessView.as_view()),
]