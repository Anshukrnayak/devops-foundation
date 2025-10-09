# config/settings/environment.py
import os

# Determine environment
ENVIRONMENT = os.getenv('DJANGO_ENVIRONMENT', 'development')

# Environment-specific settings
ENVIRONMENT_SETTINGS = {
    'development': {
        'DEBUG': True,
        'ALLOWED_HOSTS': ['localhost', '127.0.0.1', '0.0.0.0'],
        'DATABASE_URL': os.getenv('DATABASE_URL', 'postgresql://quantum:quantum@localhost:5432/quantum_trading'),
        'REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    },
    'staging': {
        'DEBUG': False,
        'ALLOWED_HOSTS': ['.your-staging-domain.com'],
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'REDIS_URL': os.getenv('REDIS_URL'),
    },
    'production': {
        'DEBUG': False,
        'ALLOWED_HOSTS': ['.your-production-domain.com'],
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'REDIS_URL': os.getenv('REDIS_URL'),
    }
}