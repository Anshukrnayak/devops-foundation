# config/settings/__init__.py
from .base import *
from .environment import ENVIRONMENT

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'staging':
    from .staging import *
else:
    from .development import *