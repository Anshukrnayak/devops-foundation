# config/settings/development.py
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '.ngrok.io', '.ngrok-free.app']

# Additional development apps
INSTALLED_APPS += [
    'debug_toolbar',
    'django_browser_reload',
]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django_browser_reload.middleware.BrowserReloadMiddleware',
]

# Debug Toolbar
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True,
}

# Database configuration for development
DATABASES['default'] = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': os.getenv('DB_NAME', 'quantum_trading_dev'),
    'USER': os.getenv('DB_USER', 'quantum'),
    'PASSWORD': os.getenv('DB_PASSWORD', 'quantum'),
    'HOST': os.getenv('DB_HOST', 'localhost'),
    'PORT': os.getenv('DB_PORT', '5432'),
}

# Email configuration for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery configuration for development
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = True

# Cache configuration for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'quantum-trading-dev',
    }
}

# Logging configuration for development
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['quantum_trading']['level'] = 'DEBUG'
LOGGING['loggers']['core']['level'] = 'DEBUG'
LOGGING['loggers']['prediction']['level'] = 'DEBUG'
LOGGING['loggers']['trading']['level'] = 'DEBUG'

# Security settings for development
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Static files for development
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Django Extensions for development
GRAPH_MODELS = {
    'all_applications': True,
    'group_models': True,
}

# Development-specific quantum trading settings
QUANTUM_TRADING.update({
    'DEBUG_MODE': True,
    'ENABLE_TEST_BROKER': True,
    'MAX_CONCURRENT_ANALYSIS': 2,
    'PREDICTION_TIMEOUT': 600,  # 10 minutes for debugging
})