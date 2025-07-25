"""
Django settings for Casino project.
"""

from pathlib import Path
import os
from django.core.management.utils import get_random_secret_key

# Environment detection
IS_PRODUCTION = os.environ.get('DJANGO_PRODUCTION', 'False').lower() == 'true'
IS_DEVELOPMENT = not IS_PRODUCTION  # Development mode is the opposite of production

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-change-this-in-production')
DEBUG = True
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'core_settings',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'axes',
    'casino',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'casino.views.LoggingMiddleware',
]

ROOT_URLCONF = 'Casino.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core_settings.context_processors.site_settings',
            ],
        },
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

WSGI_APPLICATION = 'Casino.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URL
LOGIN_URL = '/signin/'
LOGOUT_REDIRECT_URL = '/'

# Security settings for production - disabled for development
# SECURE_HSTS_SECONDS = 31536000  # 1 year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# X_FRAME_OPTIONS = 'SAMEORIGIN'
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Development settings
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Allowed hosts
ALLOWED_HOSTS = ['cashinopartners.com', 'www.cashinopartners.com', 'localhost', '127.0.0.1']

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Application definition
SITE_ID = 1

# Add additional apps to INSTALLED_APPS
INSTALLED_APPS += [
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'import_export',
    'rangefilter',
    'ckeditor',
    'crispy_forms',
    'crispy_bootstrap5',
    'robots',
    'simple_history',
    'Core',
]

# Add to existing MIDDLEWARE list
MIDDLEWARE += [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Ensure media directory exists
os.makedirs(MEDIA_ROOT, exist_ok=True)

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms Settings
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Custom error handlers
HANDLER404 = 'Core.views.handler404'
HANDLER500 = 'Core.views.handler500'
HANDLER403 = 'Core.views.handler403'
HANDLER400 = 'Core.views.handler400'

# Django Axes Configuration
# Axes Configuration
AXES_FAILURE_LIMIT = 10  # Number of failed login attempts before lockout
AXES_LOCK_OUT_AT_FAILURE = True
AXES_COOLOFF_TIME = 1  # 1 hour
AXES_LOCKOUT_TEMPLATE = 'registration/locked.html'
AXES_USE_USER_AGENT = False  # Disable user agent checking
AXES_ONLY_USER_FAILURES = True  # Only count failed attempts for the same user
AXES_RESET_ON_SUCCESS = True  # Reset failed attempts after successful login
AXES_DISABLE_ACCESS_LOG = True  # Disable access logging to avoid session_hash issues
AXES_ENABLED = True  # Enable/disable axes functionality
AXES_LOCK_OUT_BY_IP = True
AXES_LOCK_OUT_BY_USER_OR_IP = True
AXES_VERBOSE = True

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Session settings
SESSION_COOKIE_AGE = 1209600  # 2 weeks, in seconds
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Authentication URLs
LOGIN_URL = '/signin/'
LOGIN_REDIRECT_URL = '/'  # Redirect to homepage after login
LOGOUT_REDIRECT_URL = '/'  # Redirect to homepage after logout

# Jazzmin Settings
JAZZMIN_SETTINGS = {
    # title of the window (Will default to current_admin_site.site_title if absent or None)
    "site_title": "Casino Admin",
    # Title on the login screen (19 chars max) (Will default to current_admin_site.site_header if absent or None)
    "site_header": "Casino",
    # Title on the brand (19 chars max) (Will default to current_admin_site.site_header if absent or None)
    "site_brand": "Casino",
    # Logo to use for your site, must be present in static files, used for brand on top left
    "site_logo": "img/logo.png",
    # Logo to use for your site, must be present in static files, used for login form logo (defaults to site_logo)
    "login_logo": "img/logo.png",
    # CSS classes that are applied to the logo above
    "site_logo_classes": "img-circle",
    # Relative path to a favicon for your site, will default to site_logo if absent (ideally 32x32 px)
    "site_icon": "img/favicon.ico",
    # Welcome text on the login screen
    "welcome_sign": "Welcome to Casino Admin",
    # Copyright on the footer
    "copyright": "Casino Ltd",
    # The model admin to search from the search bar, search bar omitted if excluded
    "search_model": "auth.User",
    # Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
    "user_avatar": None,
    ############
    # Top Menu #
    ############
    # Links to put along the top menu
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
        {"model": "auth.User"},
        {"app": "Core"},
    ],
    #############
    # Side Menu #
    #############
    # Whether to display the side menu
    "show_sidebar": True,
    # Whether to aut expand the menu
    "navigation_expanded": True,
    # Custom icons for side menu apps/models
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "Core.sitesettings": "fas fa-cogs",
        "Core.casinouser": "fas fa-user-tie",
        "Core.pagevisit": "fas fa-chart-line",
        "Core.systemlog": "fas fa-history",
    },
    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    #############
    # UI Tweaks #
    #############
    # Relative paths to custom CSS/JS files (must be present in static files)
    "custom_css": "css/admin-custom.css",
    "custom_js": None,
    # Whether to show the UI customizer on the sidebar
    "show_ui_builder": True,
    ###############
    # Change view #
    ###############
    # Render out the change view as a single form, or in tabs, current options are
    # - single
    # - horizontal_tabs (default)
    # - vertical_tabs
    # - collapsible
    # - carousel
    "changeform_format": "horizontal_tabs",
    # override change forms on a per modeladmin basis
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
    },
    # Add a language dropdown into the admin
    "language_chooser": True,
}

# Jazzmin Configuration
JAZZMIN_SETTINGS = {
    # Title on the brand (19 chars max) (defaults to current_admin_site.site_header)
    "site_title": "Casino Admin",
    # Title on the login screen (19 chars max)
    "site_header": "Casino",
    # Title on the brand (19 chars max)
    "site_brand": "Casino Admin",
    # Logo will be handled by context processor
    # Welcome text on the login screen
    "welcome_sign": "Welcome to Casino Admin Panel",
    # Copyright on the footer
    "copyright": "Casino Ltd",
    # Field name on user model that contains avatar image
    "user_avatar": None,
    # Links to put along the top menu
    "topmenu_links": [
        # Url that gets reversed (Permissions can be added)
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        # external url that opens in a new window (Permissions can be added)
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
        # model admin to link to (Permissions checked against model)
        {"model": "auth.User"},
        # App with dropdown menu to all its models pages (Permissions checked against models)
        {"app": "casino"},
    ],
    # Custom icons for models
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
    },
    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    # Customize the look and feel of the admin
    "show_ui_builder": True,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": True,
    "footer_small_text": True,
    "body_small_text": False,
    "brand_small_text": True,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

# Logging Configuration
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
    'handlers': {
        'console': {
            'level': 'DEBUG' if not IS_PRODUCTION else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if not IS_PRODUCTION else 'ERROR',
            'propagate': True,
        },
        'Core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if not IS_PRODUCTION else 'ERROR',
            'propagate': True,
        },
    },
}

# Cache Configuration
if not IS_PRODUCTION:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
                'RETRY_ON_TIMEOUT': True,
                'MAX_CONNECTIONS': 1000,
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                'IGNORE_EXCEPTIONS': True,
            },
            'KEY_PREFIX': 'casino',
            'TIMEOUT': 300,  # 5 minutes default timeout
        }
    }

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Content Security Policy
if IS_PRODUCTION:
    CSP_DEFAULT_SRC = ("'self'",)
    CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https:", "http:")
    CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'", "https:", "http:")
    CSP_IMG_SRC = ("'self'", "data:", "https:", "http:")
    CSP_FONT_SRC = ("'self'", "https:", "http:", "data:")
    CSP_CONNECT_SRC = ("'self'", "https:", "http:")
    CSP_MEDIA_SRC = ("'self'", "https:", "http:")
    CSP_OBJECT_SRC = ("'none'",)
    CSP_FRAME_SRC = ("'self'", "https:", "http:")
    CSP_BASE_URI = ("'self'",)
    CSP_FORM_ACTION = ("'self'",)
    CSP_FRAME_ANCESTORS = ("'none'",)
    CSP_BLOCK_ALL_MIXED_CONTENT = True
    CSP_UPGRADE_INSECURE_REQUESTS = True

# Rate Limiting
RATELIMIT_ENABLE = IS_PRODUCTION
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_KEY_PREFIX = 'ratelimit'

# Maintenance Mode
MAINTENANCE_MODE = False
MAINTENANCE_MODE_IGNORE_STAFF = True
MAINTENANCE_MODE_IGNORE_SUPERUSER = True

# Cacheops Configuration (if in production)
if IS_PRODUCTION:
    CACHEOPS_REDIS = {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', 6379)),
        'db': int(os.getenv('REDIS_DB', 1)),
        'socket_timeout': 3,
    }

    CACHEOPS_DEFAULTS = {
        'timeout': 60 * 15,  # 15 minutes
        'cache_on_save': True,
    }

    CACHEOPS = {
        'Core.GameCards': {'ops': ('fetch', 'get'), 'timeout': 60 * 60},  # 1 hour
        'Core.CasinoUser': {'ops': ('fetch', 'get'), 'timeout': 60 * 30},  # 30 minutes
        'Core.SiteSettings': {'ops': ('fetch', 'get'), 'timeout': 60 * 60 * 24},  # 24 hours
    }

# Sentry Configuration (if in production)
if IS_PRODUCTION:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN', ''),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment=ENVIRONMENT,
    )
