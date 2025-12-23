import stripe
from django.conf import settings
stripe.api_key = settings.STRIPE_SECRET_KEY

def create_session(user, price_cents, currency='usd', success_url='', cancel_url='', metadata=None):
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='payment',
        line_items=[{
            'price_data': {
                'currency': currency,
                'product_data': {'name': 'Premium subscription'},
                'unit_amount': price_cents,
            },
            'quantity': 1,
        }],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata or {"user_id": str(user.id)}
    )
    return session
