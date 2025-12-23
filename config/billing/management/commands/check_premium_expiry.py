from django.core.management.base import BaseCommand
from billing.models import PremiumSubscription
from django.utils import timezone

class Command(BaseCommand):
    help = "Deactivate expired premium subscriptions"
    def handle(self, *args, **kwargs):
        now = timezone.now()
        expired = PremiumSubscription.objects.filter(is_active=True, expires_at__lte=now)
        for sub in expired:
            sub.deactivate()
            self.stdout.write(f"Deactivated {sub.user_id}")
