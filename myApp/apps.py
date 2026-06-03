from django.apps import AppConfig


class MyappConfig(AppConfig):
    name = 'myApp'

    def ready(self):
        import myApp.signals