from config.billing.models import PremiumSubscription

def user_is_premium(user):
    try:
        sub = PremiumSubscription.objects.get(user=user)
        return sub.is_valid()
    except PremiumSubscription.DoesNotExist:
        return False
