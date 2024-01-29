from django.apps import AppConfig


class ExcelAppConfig(AppConfig):
    # Конфигурация приложения Excel
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'excel_app'

    def ready(self):
        # Импорт сигналов при запуске приложения
        import excel_app.signals
