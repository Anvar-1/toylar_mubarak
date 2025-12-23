from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Message, Block, UserStatus

User = get_user_model()

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Message
        fields = [
            'id','sender','receiver','content','audio','video','timestamp',
            'delivered','seen','edited','deleted_for_all'
        ]
        read_only_fields = ['id','sender','timestamp','delivered','seen','edited','deleted_for_all']

class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = ['id','user','blocked','created_at']
        read_only_fields = ['id','user','created_at']

class UserStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStatus
        fields = ['online','last_seen']
