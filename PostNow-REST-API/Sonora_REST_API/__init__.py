# Importa a aplicação Celery para que Django possa descobrir tasks
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery não disponível - modo desenvolvimento
    pass

