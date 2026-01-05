from django.apps import AppConfig


class CampaignsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Campaigns'
    verbose_name = 'Campanhas de Marketing'
    
    def ready(self):
        """Importa signals quando app está pronto."""
        try:
            import Campaigns.signals
        except ImportError:
            pass
