from django.urls import path
from .views import PremiumStatusView, BuyPremiumMockView, AdminRevokePremiumView, buy_premium

urlpatterns = [
    path('status/', PremiumStatusView.as_view(), name='premium-status'),
    path("buy/", buy_premium),

    path('buy/mock/', BuyPremiumMockView.as_view(), name='buy-mock'),
    path('admin/revoke/<int:user_id>/', AdminRevokePremiumView.as_view(), name='revoke'),
]
