from django.apps import AppConfig


class ConfiguracionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'configuracion'
    verbose_name = 'Configuración'

    def ready(self):
        import configuracion.signals  # noqa: F401
