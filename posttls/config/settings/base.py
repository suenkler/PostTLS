"""
Django settings for PostTLS project.
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["POSTTLS_SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
if os.environ["POSTTLS_ENVIRONMENT_TYPE"] == "production":
    DEBUG = False
else:
    DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'flat',  # flat theme for django admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Custom User Model
# see: Two Scoops of Django, page 258
# see: https://www.youtube.com/watch?v=0bAJV0zNWQw
AUTH_USER_MODEL = 'core.User'


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# SSL - activate in production
if os.environ["POSTTLS_ENVIRONMENT_TYPE"] == "production":
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTOCOL", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.environ["POSTTLS_STATIC_ROOT_DIR"]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.environ["POSTTLS_MEDIA_ROOT_DIR"]

##################################################
# Settings for App PostTLS
##################################################

# email notification for mails in queue
POSTTLS_NOTIFICATION_SENDER = os.environ["POSTTLS_NOTIFICATION_SENDER"]
POSTTLS_NOTIFICATION_SMTP_HOST = os.environ["POSTTLS_NOTIFICATION_SMTP_HOST"]

# host on which the application runs
POSTTLS_TLS_HOST = os.environ["POSTTLS_TLS_HOST"]
POSTTLS_NOTIFICATION_SYSADMIN_MAIL_ADDRESS = os.environ["POSTTLS_NOTIFICATION_SYSADMIN_MAIL_ADDRESS"]
