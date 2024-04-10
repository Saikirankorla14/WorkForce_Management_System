from django.apps import AppConfig
import paypalrestsdk
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        try:
            paypalrestsdk.configure({
                "mode": "sandbox",
                "client_id": settings.RECEIVING_PAYPAL_CLIENT_ID,
                "client_secret": settings.RECEIVING_PAYPAL_CLIENT_SECRET,
            })
        except Exception as e:
            logger.error(f"Error configuring PayPal SDK: {e}")
