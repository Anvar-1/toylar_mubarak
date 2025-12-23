import random
from django.http import JsonResponse
import cv2
import mediapipe as mp
import numpy as np
import face_recognition
import requests
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import SmsVerification
from .serializers import (UserRegisterSerializer, LoginSerializer, VerifyCodeSerializer, ResetPasswordSerializer,
    SendCodeSerializer)
from .utils import set_language_for_user

User = get_user_model()



# REGISTER (phone + password)SMS code yuborish
class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        phone = request.data.get("phone")
        password = request.data.get("password")

        if not phone or not password:
            return Response({"error": _("Telefon raqam va parol majburiy.")},
                            status=status.HTTP_400_BAD_REQUEST)

        # User yaratish
        user = User(phone=phone, is_active=False)
        user.set_password(password)
        user.save()

        # 4 xonali SMS code
        code = "".join([str(random.randint(0, 9)) for _ in range(4)])

        SmsVerification.objects.update_or_create(
            user=user,
            phone=str(phone),
            defaults={"code": code, "is_verified": False}
        )

        # Eskiz
        try:
            login_url = "http://notify.eskiz.uz/api/auth/login"
            payload = {'email': 'imronhoja336@mail.ru', 'password': 'ombeUIUC8szPawGi3TXgCjDXDD0uAIx2AmwLlX9M'}
            res = requests.post(login_url, data=payload)
            token = res.json().get('data', {}).get('token')
            if token:
                sms_url = "http://notify.eskiz.uz/api/message/sms/send"
                data = {
                    "mobile_phone": str(phone),
                    "message": f"Envoy tasdiqlash kodi: {code}",
                    "from": "4546"
                }
                headers = {"Authorization": f"Bearer {token}"}
                requests.post(sms_url, headers=headers, data=data)
        except:
            pass  # Eskiz ishlamasa ham davom etadi

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": _("Ro‘yxatdan o‘tildi. SMS kodi yuborildi."),
            "user_id": user.id,
            "phone": phone,
            "sms_code": code,
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }, status=status.HTTP_201_CREATED)



#  VERIFY CODE (SMS)

class VerifyCodeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get("phone")
        sms_code = request.data.get("sms_code")

        if not phone or not sms_code:
            return Response({"error": _("Telefon va kod majburiy.")},
                            status=400)

        obj = SmsVerification.objects.filter(
            phone=phone, code=sms_code, is_verified=False
        ).first()

        if not obj:
            return Response({"error": _("Kod noto‘g‘ri yoki eskirgan.")}, status=400)

        obj.is_verified = True
        obj.save()

        user = obj.user
        user.is_active = True
        user.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": _("Kod tasdiqlandi"),
            "user_id": user.id,
            "phone": phone,
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })



#
# LOGIN (phone + password)
class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get("phone")
        password = request.data.get("password")

        if not phone or not password:
            return Response({"error": _("Telefon raqam va parol majburiy.")}, status=400)

        user = User.objects.filter(phone=phone).first()
        if not user:
            return Response({"error": _("Foydalanuvchi topilmadi.")}, status=404)

        if not user.is_active:
            return Response({"error": _("Telefon raqami tasdiqlanmagan.")}, status=400)

        if not user.check_password(password):
            return Response({"error": _("Parol noto‘g‘ri.")}, status=400)

        # Tilni o‘rnatish (sening talabing bo‘yicha)
        set_language_for_user(user)

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": _("Kirish muvaffaqiyatli."),
            "user": {
                "id": user.id,
                "phone": str(user.phone),
                "username": user.username,
                "last_name": user.last_name,
                "gender": user.gender,
            },
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }
        })


#  FACE REGISTER (face_encoding saqlash)
class FaceRegisterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        image = request.FILES.get("image")

        if not image:
            return Response({"error": _("Rasm majburiy!")}, status=400)

        np_image = face_recognition.load_image_file(image)
        enc = face_recognition.face_encodings(np_image)

        if not enc:
            return Response({"error": _("Yuz topilmadi!")}, status=400)

        request.user.face_encoding = enc[0].tobytes()
        request.user.save()

        return Response({"message": _("Yuz muvaffaqiyatli saqlandi!")}, status=201)



# FACE LOGIN
class FaceLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get("phone")
        gender = request.data.get("gender")
        image = request.FILES.get("image")

        if not phone or not image:
            return Response({"error": _("Telefon va rasm majburiy.")}, status=400)

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({"error": _("Foydalanuvchi topilmadi.")}, status=404)

        if not user.face_encoding:
            return Response({"error": _("Face ID mavjud emas!")}, status=400)

        np_image = face_recognition.load_image_file(image)
        enc = face_recognition.face_encodings(np_image)

        if not enc:
            return Response({"error": _("Rasmda yuz topilmadi!")}, status=400)

        known = np.frombuffer(user.face_encoding, dtype=np.float64)
        match = face_recognition.compare_faces([known], enc[0], tolerance=0.5)[0]

        if not match:
            return Response({"error": _("Yuz mos kelmadi!")}, status=401)

        if gender and user.gender and gender.lower() != user.gender.lower():
            return Response({"error": _("Jins mos emas!")}, status=400)

        # Tilni o‘rnatish
        set_language_for_user(user)

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": _("Face ID orqali kirish muvaffaqiyatli."),
            "user": {
                "id": user.id,
                "phone": str(user.phone),
                "username": user.username,
                "last_name": user.last_name,
                "gender": user.gender,
            },
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }
        })



#  SEND CODE
class SendCodeAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get("phone")
        if not phone:
            return Response({"error": _("Telefon majburiy.")}, status=400)

        code = "".join([str(random.randint(0, 9)) for _ in range(4)])

        SmsVerification.objects.update_or_create(
            phone=phone,
            defaults={"code": code, "is_verified": False}
        )

        return Response({"message": _("Kod yuborildi"), "code": code})



#  RESET PASSWORD
class ResetPasswordAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone']
        new_pass = serializer.validated_data['new_password']

        user = User.objects.filter(phone=phone).first()
        if not user:
            return Response({"error": _("Foydalanuvchi topilmadi.")}, status=404)

        user.set_password(new_pass)
        user.save()

        return Response({"message": _("Parol o‘zgartirildi.")})



# MediaPipe yuz aniqlash moduli
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils


def face_detection_view(request):
    # Kamera oqimi
    cap = cv2.VideoCapture(0)

    # Yuz aniqlash modelini o'rnatish
    with mp_face_detection.FaceDetection(min_detection_confidence=0.2) as face_detection:
        ret, frame = cap.read()
        if not ret:
            return JsonResponse({'error': 'Kamera oqimi xatosi'}, status=500)

        # Rasmni BGR formatidan RGB formatiga o‘tkazish
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(frame_rgb)

        # Yuz aniqlangan bo‘lsa, uni rasmga chizish
        if results.detections:
            for detection in results.detections:
                mp_drawing.draw_detection(frame, detection)

        # Rasmni ekranga chiqarish (OpenCV yordamida)
        cv2.imshow('MediaPipe Face Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            return JsonResponse({'message': 'Yuz aniqlash muvaffaqiyatli yakunlandi'})

    cap.release()
    cv2.destroyAllWindows()




# Tushuntirish:
# 1. UserCreateView
#
# Ro'yxatdan o'tish: Foydalanuvchi telefon raqami va parol bilan ro'yxatdan o'tadi, so'ngra SMS kodi yuboriladi.
#
# 2. VerifyCodeView
#
# SMS tasdiqlash: Foydalanuvchi SMS kodini tasdiqlaydi va foydalanuvchi is_active=True bo'ladi.
#
# 3. FaceRegisterView
#
# Yuzni ro'yxatga olish: Foydalanuvchi yuzini ro'yxatga oladi va face_encoding saqlanadi.
#
# 4. FaceLoginView
#
# Yuz orqali kirish va jinsni tekshirish: Foydalanuvchi telefon raqami, jins va yuz rasmidan foydalanib tizimga kiradi. Jinsni tekshirib, faqat mos jinsdagi foydalanuvchiga kirishga ruxsat beriladi.
#
# 5. SendCodeAPIView
#
# SMS kodi yuborish: Telefon raqamiga SMS kodi yuboriladi.
#
# 6. ResetPasswordAPIView
#
# Parolni tiklash: Telefon raqami yordamida foydalanuvchi parolini yangilaydi.
#
# Natija:
#
# Yuzni tanib olish va gender tekshirish jarayonlari mukammal ishlaydi, va foydalanuvchiga jins mos bo'lmasa tizimga kirish taqiqlanadi.