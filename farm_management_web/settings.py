"""
Django settings for farm_management_web project.

Generated by 'django-admin startproject' using Django 4.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import dotenv
dotenv.load_dotenv()
from pathlib import Path
import os
from django.core.management.utils import get_random_secret_key
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

LOGIN_URL = '/login/'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_random_secret_key()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

print(f"__file__: {__file__}")
BASE_DIR = Path(__file__).resolve().parent.parent
print(f"BASE_DIR: {BASE_DIR}")

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main.apps.MainConfig',
    'crispy_forms',
    'crispy_bootstrap5',
    'fontawesomefree',
    'channels',
    'channels_redis',
    'debug_toolbar',
    'widget_tweaks',
    'django_q',
    'mathfilters',
    'storages',
    
]

ASGI_APPLICATION = "farm_management_web.routing.application"

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6380)],
        },
    },
}

CRISPY_ALLOWED_TEMPLATE_PACK = 'bootstrap5'

CRISPY_TEMPLATE_PACK = 'bootstrap5'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # 'channels.middleware.WebSocketMiddleware'
]

ROOT_URLCONF = 'farm_management_web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'main/static'),
    os.path.join(BASE_DIR, 'static/widget_tweaks'),
    os.path.join(BASE_DIR, 'static/vendor/jquery-ui'),
    os.path.join(BASE_DIR, 'static/vendor/bootstrap'),
    os.path.join(BASE_DIR, 'static/vendor/bootstrap-select'),
    os.path.join(BASE_DIR, 'static/vendor/bootstrap-table'),
    os.path.join(BASE_DIR, 'static/vendor/flatpickr'),
    os.path.join(BASE_DIR, 'static/vendor/font-awesome'),
    os.path.join(BASE_DIR, 'static/vendor/jquery-confirm'),
    os.path.join(BASE_DIR, 'static/vendor/malihu-custom-scrollbar-plugin'),
]

WSGI_APPLICATION = 'farm_management_web.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.getenv('DB_NAME'),
#         'USER': os.getenv('DB_USER'),
#         'PASSWORD': os.getenv('DB_PASSWORD'),
#         'HOST': os.getenv('DB_HOST'),
#         'PORT': os.getenv('DB_PORT'),
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Additional directories to look for static files during development
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Directory where collected static files will be stored
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
SECURE_CROSS_ORIGIN_OPENER_POLICY='same-origin-allow-popups'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'main.CustomUser'

# URL to redirect to after changing the password
PASSWORD_RESET_COMPLETE = '/login'
RECEIVING_PAYPAL_CLIENT_ID = 'AfuJfzHChbHucGFxQkML3GhosCN4xNhZR7wzqF8oWvgw9R6k6YcHOo3J1IsGCzYV1NP6Qig1ccnZQcCE'
RECEIVING_PAYPAL_CLIENT_SECRET = 'EF9DrFKJz1m46-I9UOptVCV9HVmjNnyYwnreynjscMx5N9mmDJkaiLvI5J6jVfHDcK-b-k-tPzgKrEr0'
#  set up to send emails 
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_USE_TLS = True    
# EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'korlasaikiran8@gmail.com'
EMAIL_HOST_PASSWORD = 'zwcz tlmy mgmc vssn'
# EMAIL_PORT = '2525'
PAYPAL_CLIENT_ID = 'AfuJfzHChbHucGFxQkML3GhosCN4xNhZR7wzqF8oWvgw9R6k6YcHOo3J1IsGCzYV1NP6Qig1ccnZQcCE'
PAYPAL_SECRET = 'EF9DrFKJz1m46-I9UOptVCV9HVmjNnyYwnreynjscMx5N9mmDJkaiLvI5J6jVfHDcK-b-k-tPzgKrEr0'
PAYPAL_ACCESS_TOKEN = 'A21AAJcZ-zMt_DEqbxAXMqrv8S8jKS36VfrjIQyDfvqxWhGrZPQwxemp1RdeM0sfAEIAlPUETWE8BXe8Bgn6L43Lrwd0Hd0Wg'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'channels': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

Q_CLUSTER = {
    'name': 'DjangORM',
    'workers': 4,
    'timeout': 90,
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',
}