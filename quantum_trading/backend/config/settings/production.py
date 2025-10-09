# config/settings/production.py
from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

DEBUG = False

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Database configuration
DATABASES['default'] = dj_database_url.config(
    conn_max_age=600,
    conn_health_checks=True,
    ssl_require=True,
)

# Redis configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL')
CACHES['default']['LOCATION'] = os.getenv('REDIS_URL')

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Quantum Trading <noreply@quantumtrading.com>')

# Logging configuration for production
LOGGING['handlers']['file']['filename'] = '/var/log/quantum_trading/app.log'
LOGGING['handlers']['error_file']['filename'] = '/var/log/quantum_trading/errors.log'
LOGGING['handlers']['celery_file']['filename'] = '/var/log/quantum_trading/celery.log'

# Remove console handler in production
for logger in LOGGING['loggers'].values():
    if 'console' in logger.get('handlers', []):
        logger['handlers'].remove('console')

# Sentry Configuration
if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=0.1,
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True,
        environment=os.getenv('SENTRY_ENVIRONMENT', 'production'),
    )

# Static files for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# CORS settings for production
CORS_ALLOWED_ORIGINS = [
    "https://your-production-domain.com",
    "https://www.your-production-domain.com",
]

# Production-specific quantum trading settings
QUANTUM_TRADING.update({
    'DEBUG_MODE': False,
    'ENABLE_TEST_BROKER': False,
    'MAX_CONCURRENT_ANALYSIS': 10,
    'PREDICTION_TIMEOUT': 180,  # 3 minutes
    'DATA_RETENTION_DAYS': 30,
})

# Performance optimizations
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Cache timeouts
CACHE_MIDDLEWARE_SECONDS = 300  # 5 minutes

# Security headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')