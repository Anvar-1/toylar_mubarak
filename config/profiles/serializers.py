from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', required=False)

    class Meta:
        model = Profile
        fields = [
            'username', 'last_name', 'email',
            'birth_day', 'age', 'children', 'gender',
            'city', 'region', 'user_img', 'interests'
        ]

    def update(self, instance, validated_data):
        user_fields = {}

        # Userga tegishli fieldlarni ajratamiz
        for field in ['username', 'last_name', 'email']:
            if 'user' in validated_data and field in validated_data['user']:
                user_fields[field] = validated_data['user'][field]

        # Profil maydonlarini yangilash
        profile_fields = {k: v for k, v in validated_data.items() if k != 'user'}

        for attr, value in profile_fields.items():
            setattr(instance, attr, value)

        instance.save()

        # User maydonlarini yangilash
        user = instance.user
        for attr, value in user_fields.items():
            setattr(user, attr, value)
        user.save()

        return instance

