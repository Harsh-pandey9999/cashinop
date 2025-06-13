from .settings import *
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Hardcoded secret key for production (you should change this to a secure value later)
SECRET_KEY = 'django-insecure-hardcoded-key-for-production-change-this-later'

# Domain hardcoded for production
ALLOWED_HOSTS = ['cashinopartners.com', 'www.cashinopartners.com']

# CSRF Trusted Origins for production
CSRF_TRUSTED_ORIGINS = ['http://cashinopartners.com', 'https://cashinopartners.com', 'http://www.cashinopartners.com', 'https://www.cashinopartners.com']

# Security settings - Adjusted for production environment without HTTPS
# If your server uses HTTPS, set these to True
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0  # Disabled until HTTPS is properly configured
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False  # Set to False if not using HTTPS
CSRF_COOKIE_SECURE = False  # Set to False if not using HTTPS
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'SAMEORIGIN'  # Changed from DENY to allow admin iframes

# Static files configuration
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'staticfiles/media')
MEDIA_URL = 'static/media/'

# Use whitenoise for static files serving
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MIDDLEWARE = ['whitenoise.middleware.WhiteNoiseMiddleware'] + MIDDLEWARE

# Configure WhiteNoise to serve media files in production
WHITENOISE_AUTOREFRESH = True
WHITENOISE_USE_FINDERS = False

# Session settings
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 86400  # 24 hours in seconds
SESSION_SAVE_EVERY_REQUEST = True

# Database configuration hardcoded for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        # If you're using MySQL or PostgreSQL in production, uncomment and fill these:
        # 'ENGINE': 'django.db.backends.mysql',
        # 'NAME': 'casino_db',
        # 'USER': 'casino_user',
        # 'PASSWORD': 'your_database_password',
        # 'HOST': 'localhost',
        # 'PORT': '3306',
    }
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/django-error.log'),
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'casino': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Email configuration hardcoded for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'  # Replace with your actual email
EMAIL_HOST_PASSWORD = 'your-app-password'  # Replace with your actual app password
DEFAULT_FROM_EMAIL = 'noreply@cashinopartners.com'

# Ensure logs directory exists
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)
