from django.urls import path
from .views import (
    MessageListAPIView, MessageCreateView, MessageDeleteView,
    MessageDeleteForAllView, MessageSeenView, MessageEditView,
    BlockUserView, UserStatusView
)

urlpatterns = [
    path('messages/', MessageListAPIView.as_view(), name='message_list'),
    path('send/', MessageCreateView.as_view(), name='send_message'),
    path('messages/<int:pk>/delete/', MessageDeleteView.as_view(), name='message_delete'),
    path('messages/<int:pk>/delete_for_all/', MessageDeleteForAllView.as_view(), name='message_delete_for_all'),
    path('messages/<int:pk>/seen/', MessageSeenView.as_view(), name='message_seen'),
    path('messages/<int:pk>/edit/', MessageEditView.as_view(), name='message_edit'),
    path('block/', BlockUserView.as_view(), name='block_user'),
    path('status/<int:user_id>/', UserStatusView.as_view(), name='user_status'),
]

