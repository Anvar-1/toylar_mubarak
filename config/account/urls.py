from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from .views import (
    UserCreateView, LoginAPIView, SendCodeAPIView, VerifyCodeView,
    ResetPasswordAPIView, FaceRegisterView, FaceLoginView
)

urlpatterns = [
    path('register/', UserCreateView.as_view(), name='user-register'),
    path('login/', LoginAPIView.as_view(), name='user-login'),
    path('face/register/', FaceRegisterView.as_view(), name='face-register'),
    path('face-detection/', views.face_detection_view, name='face_detection'),
    path('face/login/', FaceLoginView.as_view(), name='face-login'),
    path('send-code/', SendCodeAPIView.as_view(), name='send-code'),
    path('verify-code/', VerifyCodeView.as_view(), name='verify-code'),
    path('reset-password/', ResetPasswordAPIView.as_view(), name='reset-password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
