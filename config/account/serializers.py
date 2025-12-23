from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import SmsVerification
import random
import requests

User = get_user_model()


class SendCodeSerializer(serializers.Serializer):
    phone = serializers.CharField()


    @staticmethod
    def send_verification_code(phone):
        code = "".join([str(random.randint(0, 9)) for _ in range(4)])

        # Eskiz
        login_url = "http://notify.eskiz.uz/api/auth/login"
        payload = {
            'email': 'imronhoja336@mail.ru',
            'password': 'ombeUIUC8szPawGi3TXgCjDXDD0uAIx2AmwLlX9M'
        }
        res = requests.post(login_url, data=payload)
        token = res.json().get('data', {}).get('token', None)

        if not token:
            raise ValidationError("Eskiz API bilan bog‘lanishda xatolik.")

        sms_url = "http://notify.eskiz.uz/api/message/sms/send"
        sms_payload = {
            'mobile_phone': str(phone),
            'message': f"Envoy tasdiqlash kodi: {code}",
            'from': '4546',
            'callback_url': 'http://0000.uz/test.php'
        }

        headers = {'Authorization': f"Bearer {token}"}
        requests.post(sms_url, headers=headers, data=sms_payload)

        SmsVerification.objects.update_or_create(
            phone=phone, defaults={"code": code, "is_verified": False}
        )

        return code



class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "phone", "password",
            "username", "last_name", "gender",
            "birth_day", "city", "region",
            "email", "children", "interests"
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create(**validated_data, is_active=False)
        user.set_password(password)
        user.save()
        return user



class VerifyCodeSerializer(serializers.Serializer):
    phone = serializers.CharField()
    sms_code = serializers.CharField()


    def validate(self, attrs):
        phone = attrs["phone"]
        code = attrs["sms_code"]

        obj = SmsVerification.objects.filter(
            phone=phone, code=code, is_verified=False
        ).first()

        if not obj:
            raise serializers.ValidationError("Kod noto‘g‘ri yoki eskirgan.")

        obj.is_verified = True
        obj.save()

        user = obj.user
        user.is_active = True
        user.save()

        attrs["user"] = user
        return attrs


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    last_name = serializers.CharField()
    gender = serializers.CharField()
    password = serializers.CharField()


    def validate(self, data):
        phone = data["phone"]
        password = data["password"]

        user = User.objects.filter(phone=phone).first()
        if not user:
            raise ValidationError("Foydalanuvchi topilmadi.")

        if not user.is_active:
            raise ValidationError("Telefon raqami tasdiqlanmagan.")

        if not user.check_password(password):
            raise ValidationError("Parol noto‘g‘ri.")

        data["user"] = user
        return data


class ResetPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise ValidationError("Parollar mos emas.")
        return data


class FaceRegisterSerializer(serializers.Serializer):
    image = serializers.ImageField()
