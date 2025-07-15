from django.apps import AppConfig

class CoreSettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core_settings'
    
    def ready(self):
        # Import signals to register them
        import core_settings.signals
