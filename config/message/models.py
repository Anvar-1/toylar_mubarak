from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    content = models.TextField(blank=True, null=True)
    audio = models.FileField(upload_to="chat_audio/", blank=True, null=True)
    video = models.FileField(upload_to="chat_video/", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # status
    delivered = models.BooleanField(default=False)
    seen = models.BooleanField(default=False)
    edited = models.BooleanField(default=False)
    deleted_for_all = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} → {self.receiver}: ({self.timestamp:%Y-%m-%d %H:%M})"

class Block(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocker_set")
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocked_set")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "blocked")

    def __str__(self):
        return f"{self.user} blocked {self.blocked}"

class UserStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='status')
    last_seen = models.DateTimeField(null=True, blank=True)
    online = models.BooleanField(default=False)

    def mark_online(self):
        self.online = True
        self.last_seen = timezone.now()
        self.save(update_fields=['online','last_seen'])

    def mark_offline(self):
        self.online = False
        self.last_seen = timezone.now()
        self.save(update_fields=['online','last_seen'])

    def __str__(self):
        return f"{self.user} status"
