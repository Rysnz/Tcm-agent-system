from celery import Celery

# Create Celery app instance
app = Celery('tcm_agent')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered apps
app.autodiscover_tasks()
