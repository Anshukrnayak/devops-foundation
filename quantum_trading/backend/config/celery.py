# backend/config/celery.py
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

app = Celery('quantum_trading')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Task routing configuration
app.conf.task_routes = {
    'prediction.tasks.*': {'queue': 'predictions'},
    'core.tasks.fetch_market_data': {'queue': 'market_data'},
    'core.tasks.calculate_indicators': {'queue': 'indicators'},
    'trading.tasks.*': {'queue': 'trading'},
}

# Task serialization
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

# Rate limiting
app.conf.task_annotations = {
    'prediction.tasks.run_quantum_analysis': {'rate_limit': '10/m'},
    'core.tasks.fetch_market_data': {'rate_limit': '100/m'},
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')