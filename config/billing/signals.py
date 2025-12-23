from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import PremiumSubscription
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json

channel_layer = get_channel_layer()

@receiver(post_save, sender=PremiumSubscription)
def send_premium_update(sender, instance, created, **kwargs):
    """
    Foydalanuvchi premium bo'lib qolsa yoki bekor qilinsa, frontendlarni ogohlantirish.
    Biz individual kanallarga yuboramiz: user_<id>
    """
    payload = {
        "type": "premium.update",
        "user_id": instance.user.id,
        "is_premium": instance.is_valid(),
        "expires_at": instance.expires_at.isoformat() if instance.expires_at else None
    }
    # individual user group
    group = f"user_{instance.user.id}"
    async_to_sync(channel_layer.group_send)(group, {"type": "broadcast", "payload": payload})
