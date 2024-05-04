"""
WSGI config for farm_management_web project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

<<<<<<< HEAD
settings_module = 'farm_management_web.deployment' if 'WEBSITE_HOSTNAME' in os.environ else 'farm_management_web.settings'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
=======
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm_management_web.settings')
>>>>>>> 0934cdc065be7610754eed0b08bec2b0ef44105c

application = get_wsgi_application()
