from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import PremiumSubscription
from .serializers import PremiumSubscriptionSerializer
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from rest_framework import status

class PremiumStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub, _ = PremiumSubscription.objects.get_or_create(user=request.user)
        ser = PremiumSubscriptionSerializer(sub)
        return Response(ser.data)

class BuyPremiumMockView(APIView):
    """
    TEST endpoint (development) - for testing without payment provider.
    body: {"months":1}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        months = int(request.data.get("months", 1))
        sub, _ = PremiumSubscription.objects.get_or_create(user=request.user)
        sub.is_active = True
        sub.bought_at = timezone.now()
        sub.expires_at = timezone.now() + relativedelta(months=months)
        sub.provider = "mock"
        sub.provider_payment_id = f"mock-{request.user.id}-{int(time.time())}"
        sub.save()
        return Response({"detail":"premium activated", "expires_at": sub.expires_at}, status=status.HTTP_200_OK)

class AdminRevokePremiumView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        try:
            sub = PremiumSubscription.objects.get(user__id=user_id)
            sub.deactivate()
            return Response({"detail":"revoked"})
        except PremiumSubscription.DoesNotExist:
            return Response({"detail":"not found"}, status=status.HTTP_404_NOT_FOUND)
