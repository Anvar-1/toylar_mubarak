from rest_framework import serializers
from .models import PremiumSubscription

class PremiumSubscriptionSerializer(serializers.ModelSerializer):
    days_left = serializers.SerializerMethodField()
    class Meta:
        model = PremiumSubscription
        fields = ['is_active', 'bought_at', 'expires_at', 'days_left', 'provider', 'provider_payment_id']

    def get_days_left(self, obj):
        return obj.days_left()
