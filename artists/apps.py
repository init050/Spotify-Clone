from django.apps import AppConfig


class ArtistsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'artists'

    def ready(self):
        # Import signals so they are connected when the app is ready.
        import artists.signals
