from django.apps import AppConfig


class PstConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pst'

    def ready(self):
        import pst.signals
