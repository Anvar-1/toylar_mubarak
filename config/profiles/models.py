from django.db import models
from django.conf import settings
from datetime import date

User = settings.AUTH_USER_MODEL

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_img = models.ImageField(upload_to='profiles/', null=True, blank=True)
    interests = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    birth_day = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    children = models.CharField(max_length=50, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.birth_day:
            today = date.today()
            self.age = today.year - self.birth_day.year - (
                (today.month, today.day) < (self.birth_day.month, self.birth_day.day)
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.phone} profili"





