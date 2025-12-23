import json
import os
import time
import base64
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import Message, Block, UserStatus
from config.billing.models import PremiumSubscription

User = get_user_model()

# ======================================================================
# =========================== PREMIUM CHECK =============================
# ======================================================================

@database_sync_to_async
def user_is_premium(user):
    try:
        sub = PremiumSubscription.objects.get(user=user)
        return sub.is_valid()
    except PremiumSubscription.DoesNotExist:
        return False


# ======================================================================
# =========================== HELPER FUNCTIONS ==========================
# ======================================================================

@database_sync_to_async
def save_file_from_base64(b64str, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64str))
    return path


@database_sync_to_async
def get_user_by_id(user_id):
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return None


@database_sync_to_async
def is_blocked(user_from, user_to):
    return (
        Block.objects.filter(user=user_to, blocked=user_from).exists() or
        Block.objects.filter(user=user_from, blocked=user_to).exists()
    )


@database_sync_to_async
def create_message_db(sender, receiver, text, audio_path=None, video_path=None):
    msg = Message(sender=sender, receiver=receiver, content=text or "")
    if audio_path:
        msg.audio.name = audio_path
    if video_path:
        msg.video.name = video_path
    msg.save()
    return msg


@database_sync_to_async
def mark_delivered_db(msg_id):
    try:
        msg = Message.objects.get(pk=msg_id)
        msg.delivered = True
        msg.save(update_fields=['delivered'])
    except:
        pass


@database_sync_to_async
def mark_online(user):
    status = getattr(user, "status", None)
    if status:
        status.mark_online()


@database_sync_to_async
def mark_offline(user):
    status = getattr(user, "status", None)
    if status:
        status.mark_offline()


# ======================================================================
# =========================== CHAT CONSUMER =============================
# ======================================================================

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope.get("user")

        if not user or user.is_anonymous:
            return await self.close()

        self.user = user
        self.room_group_name = f"user_{user.id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await mark_online(self.user)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await mark_offline(self.user)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except:
            return await self.send_json({"error": "Invalid JSON"})

        action = data.get("action")

        if action == "typing":
            return await self._handle_typing(data)

        if action == "edit":
            return await self._handle_edit(data)

        if action == "delete_for_all":
            return await self._handle_delete_for_all(data)

        if action in ["call_offer", "call_answer", "ice_candidate"]:
            return await self._handle_call_signaling(data)

        return await self._handle_message_send(data)

    # -------------------- Typing (Premium) --------------------------
    async def _handle_typing(self, data):
        receiver_id = data.get("receiver")
        receiver = await get_user_by_id(receiver_id)

        if not receiver:
            return

        # 🔥 Typing faqat PREMIUM uchun
        if not await user_is_premium(self.user):
            return await self.send_json({"error": "typing is premium feature"})

        await self.channel_layer.group_send(
            f"user_{receiver.id}",
            {
                "type": "typing_signal",
                "sender_id": self.user.id,
                "sender_username": self.user.username,
            },
        )

    # -------------------- Edit message ------------------------------
    async def _handle_edit(self, data):
        msg_id = data.get("message_id")
        new_text = data.get("content")

        updated = await self._edit_message(msg_id, new_text)
        if not updated:
            return await self.send_json({"error": "message not found or no permission"})

        await self.channel_layer.group_send(
            f"user_{updated.receiver.id}",
            {
                "type": "message_edited",
                "message_id": updated.id,
                "content": updated.content,
            },
        )

        await self.send_json({"status": "edited", "message_id": updated.id})

    # -------------------- Delete for all ----------------------------
    async def _handle_delete_for_all(self, data):
        msg_id = data.get("message_id")
        deleted = await self._delete_for_all(msg_id)

        if not deleted:
            return await self.send_json({"error": "no permission or message missing"})

        await self.channel_layer.group_send(
            f"user_{deleted.receiver.id}",
            {"type": "message_deleted", "message_id": deleted.id},
        )

        await self.send_json({"status": "deleted_for_all", "message_id": deleted.id})

    # -------------------- Send message ------------------------------
    async def _handle_message_send(self, data):
        receiver_id = data.get("receiver")
        receiver = await get_user_by_id(receiver_id)

        if not receiver:
            return await self.send_json({"error": "receiver not found"})

        if await is_blocked(self.user, receiver):
            return await self.send_json({"error": "blocked"})

        text = data.get("message")
        audio_b64 = data.get("audio")
        video_b64 = data.get("video")

        audio_path = video_path = None

        if audio_b64:
            filename = f"chat_audio/{self.user.id}_{int(time.time())}.wav"
            path = os.path.join(settings.MEDIA_ROOT, filename)
            await save_file_from_base64(audio_b64, path)
            audio_path = filename

        if video_b64:
            filename = f"chat_video/{self.user.id}_{int(time.time())}.mp4"
            path = os.path.join(settings.MEDIA_ROOT, filename)
            await save_file_from_base64(video_b64, path)
            video_path = filename

        msg_obj = await create_message_db(self.user, receiver, text, audio_path, video_path)

        await self.channel_layer.group_send(
            f"user_{receiver.id}",
            {
                "type": "chat.message",
                "message_id": msg_obj.id,
                "sender_id": self.user.id,
                "message": msg_obj.content,
                "audio": msg_obj.audio.url if msg_obj.audio else None,
                "video": msg_obj.video.url if msg_obj.video else None,
                "timestamp": msg_obj.timestamp.isoformat(),
            },
        )

        await mark_delivered_db(msg_obj.id)

        await self.send_json({"status": "sent", "message_id": msg_obj.id})

    # -------------------- Call signaling ----------------------------
    async def _handle_call_signaling(self, data):
        receiver_id = data.get("receiver")

        receiver = await get_user_by_id(receiver_id)
        if not receiver:
            return await self.send_json({"error": "receiver not found"})

        action = data["action"]

        payload = {"sender_id": self.user.id}

        if action == "call_offer":
            payload.update({"type": "call.offer", "offer": data["offer"]})

        elif action == "call_answer":
            payload.update({"type": "call.answer", "answer": data["answer"]})

        elif action == "ice_candidate":
            payload.update({"type": "call.ice", "candidate": data["candidate"]})

        await self.channel_layer.group_send(f"user_{receiver.id}", payload)

    # -------------------- Event Handlers ----------------------------
    async def chat_message(self, event):
        await self.send_json(event)

    async def typing_signal(self, event):
        await self.send_json(event)

    async def message_edited(self, event):
        await self.send_json(event)

    async def message_deleted(self, event):
        await self.send_json(event)

    async def call_offer(self, event):
        await self.send_json(event)

    async def call_answer(self, event):
        await self.send_json(event)

    async def call_ice(self, event):
        await self.send_json(event)

    # -------------------- DB Helpers ------------------------------
    @database_sync_to_async
    def _edit_message(self, msg_id, new_text):
        try:
            msg = Message.objects.get(pk=msg_id)
            if msg.sender_id != self.user.id:
                return None
            msg.content = new_text
            msg.edited = True
            msg.save()
            return msg
        except:
            return None

    @database_sync_to_async
    def _delete_for_all(self, msg_id):
        try:
            msg = Message.objects.get(pk=msg_id)
            if msg.sender_id != self.user.id:
                return None

            msg.deleted_for_all = True
            msg.content = ""

            if msg.audio:
                msg.audio.delete(save=False)
            if msg.video:
                msg.video.delete(save=False)

            msg.save()
            return msg
        except:
            return None

    async def send_json(self, data):
        await self.send(text_data=json.dumps(data))


# ======================================================================
# =========================== CALL CONSUMER =============================
# ======================================================================

class CallConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"call_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "call_message", "data": data},
        )

    async def call_message(self, event):
        await self.send(text_data=json.dumps(event["data"]))


