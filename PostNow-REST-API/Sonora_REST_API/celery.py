import os
from celery import Celery

# Define o módulo de configuração Django padrão
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sonora_REST_API.settings')

# Cria a aplicação Celery
app = Celery('Sonora_REST_API')

# Carrega configurações do Django usando o namespace 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descobre tasks em todos os apps Django registrados
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Task de debug para testar se o Celery está funcionando."""
    print(f'Request: {self.request!r}')

