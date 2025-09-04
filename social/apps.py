from django.apps import AppConfig


class SocialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'social'

    def ready(self):
        '''
        Import signals so they are connected when the app is ready.
        '''
        import social.signals
