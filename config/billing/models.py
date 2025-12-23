from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class PremiumSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='premium')
    is_active = models.BooleanField(default=False)
    bought_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    provider = models.CharField(max_length=50, blank=True, null=True)
    provider_payment_id = models.CharField(max_length=255, blank=True, null=True)

    def is_valid(self):
        return self.is_active and self.expires_at and timezone.now() < self.expires_at

    def days_left(self):
        if not self.expires_at:
            return 0
        delta = self.expires_at - timezone.now()
        return max(0, delta.days)

    def activate(self, duration_days:int=30, provider=None, provider_payment_id=None):
        self.is_active = True
        self.bought_at = timezone.now()
        self.expires_at = timezone.now() + timezone.timedelta(days=duration_days)
        if provider:
            self.provider = provider
        if provider_payment_id:
            self.provider_payment_id = provider_payment_id
        self.save()

    def deactivate(self):
        self.is_active = False
        self.save()

    def __str__(self):
        return f"Premium({self.user}) active={self.is_active} expires={self.expires_at}"
