from django.apps import AppConfig

class SocknetConfig(AppConfig):
    name = 'socknet'

    def ready(self):
        import socknet.signals
