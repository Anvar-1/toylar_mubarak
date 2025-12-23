from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Message, Block, UserStatus
from .serializers import MessageSerializer, BlockSerializer, UserStatusSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

# Tasdiqlangan foydalanuvchi uchun xabarlar roʻyxati
class MessageListAPIView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # ixtiyoriy ravishda ?with_deleted=true ga ham oʻchirilgan_hammasini koʻrsatishga ruxsat berish
        show_deleted = self.request.query_params.get("with_deleted") == "true"
        qs = Message.objects.filter(receiver=self.request.user)
        if not show_deleted:
            qs = qs.filter(deleted_for_all=False)
        return qs.order_by('-timestamp')

# Xabar yaratish
class MessageCreateView(generics.CreateAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        receiver = serializer.validated_data.get('receiver')
        # check blocks: if receiver blocked sender OR sender blocked receiver -> forbidden
        if Block.objects.filter(user=receiver, blocked=self.request.user).exists():
            return Response({"error":"Sizni foydalanuvchi bloklagan."}, status=status.HTTP_403_FORBIDDEN)
        if Block.objects.filter(user=self.request.user, blocked=receiver).exists():
            return Response({"error":"Siz bu foydalanuvchini bloklagansiz."}, status=status.HTTP_403_FORBIDDEN)

        serializer.save(sender=self.request.user)

# Oʻchirish (faqat joʻnatuvchi xabarni mahalliy darajada oʻchirib tashlashi mumkin)
class MessageDeleteView(generics.DestroyAPIView):
    queryset = Message.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        message = self.get_object()
        if message.sender != request.user:
            return Response({"error": "Siz bu xabarni o'chira olmaysiz"}, status=403)
        return super().delete(request, *args, **kwargs)

# Hamma uchun o'chirish (faqat jo'natuvchiga mumkin)
class MessageDeleteForAllView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        msg = get_object_or_404(Message, pk=pk)
        if msg.sender != request.user:
            return Response({"error":"Siz bu amalni bajara olmaysiz."}, status=403)
        msg.deleted_for_all = True
        msg.content = ""
        # media fayllar havolalarini olib tashlash
        msg.audio.delete(save=False)
        msg.video.delete(save=False)
        msg.save()
        # ixtiyoriy: qabul qiluvchini kanallar orqali xabardor qilish
        return Response({"status":"deleted_for_all"})

class MessageSeenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        msg = get_object_or_404(Message, pk=pk, receiver=request.user)
        msg.seen = True
        msg.save(update_fields=['seen'])
        return Response({"status":"seen"})

# Edit message
class MessageEditView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        msg = get_object_or_404(Message, pk=pk, sender=request.user)
        if msg.deleted_for_all:
            return Response({"error":"Xabar o‘chirib yuborilgan."}, status=400)
        new_content = request.data.get('content', '').strip()
        msg.content = new_content
        msg.edited = True
        msg.save(update_fields=['content','edited'])
        return Response({"status":"edited","message":new_content})

# Block
class BlockUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        blocked_id = request.data.get("blocked")
        if not blocked_id:
            return Response({"error":"blocked user id required"}, status=400)
        if int(blocked_id) == request.user.id:
            return Response({"error":"Siz o'zingizni bloklay olmaysiz."}, status=400)
        blocked_user = get_object_or_404(User, pk=blocked_id)
        obj, created = Block.objects.get_or_create(user=request.user, blocked=blocked_user)
        return Response({"status":"blocked" if created else "already_blocked"})

    def delete(self, request):
        blocked_id = request.data.get("blocked")
        blocked_user = get_object_or_404(User, pk=blocked_id)
        Block.objects.filter(user=request.user, blocked=blocked_user).delete()
        return Response({"status":"unblocked"})

class UserStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        status_obj = getattr(user, 'status', None)
        if not status_obj:
            return Response({"online": False, "last_seen": None})
        ser = UserStatusSerializer(status_obj)
        return Response(ser.data)
