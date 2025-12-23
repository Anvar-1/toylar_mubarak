from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


LANGUAGE_CHOICES = [
    ('uz', "O‘zbekcha"),
    ('ru', "Русский"),
    ('en', "English"),
]


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Phone number is required")

        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(phone, password, **extra_fields)


class User(AbstractUser):
    username = None  # 🚨 MUHIM: username butunlay olib tashlanadi

    phone = PhoneNumberField(unique=True)

    last_name = models.CharField(max_length=150, blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Erkak'), ('female', 'Ayol')],
        null=True,
        blank=True
    )
    birth_day = models.DateField(null=True, blank=True)
    children = models.CharField(max_length=10, null=True, blank=True)
    city = models.CharField(max_length=120, null=True, blank=True)
    region = models.CharField(max_length=120, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    interests = models.TextField(null=True, blank=True)
    face_encoding = models.BinaryField(null=True, blank=True)

    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='uz'
    )

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    objects = UserManager()  # 🔥 ENG MUHIM QATOR

    def __str__(self):
        return str(self.phone)


class SmsVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    phone = PhoneNumberField()
    code = models.CharField(max_length=4)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.phone} - {self.code}"
