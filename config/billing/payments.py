import hashlib
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from .models import PremiumSubscription
from django.utils import timezone
import json

@csrf_exempt
def click_notify(request):
    data = json.loads(request.body)
    # Click to'lovlar uchun signature verify (Click dokumentatsiyasiga qarang)
    # misol uchun: sign = data.get('sign')
    # verify logic...
    if valid:
        user_id = data['user_id']
        months = int(data.get('months', 1))
        # activate
        sub, _ = PremiumSubscription.objects.get_or_create(user_id=user_id)
        sub.activate(duration_days=30*months, provider='click', provider_payment_id=data.get('click_trans_id'))
        return JsonResponse({'result': 'ok'})
    return JsonResponse({'error':'invalid'}, status=400)

@csrf_exempt
def payme_notify(request):
    # Payme uses JSON-RPC 2.0 style - respond with proper id and result
    payload = json.loads(request.body)
    method = payload.get('method')
    # handle checkPerformTransaction, createTransaction, performTransaction, etc.
    # see Payme docs
    return JsonResponse({"result": {}})
