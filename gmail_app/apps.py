from django.apps import AppConfig
import logging
import os

logger = logging.getLogger('gmail_app')

# Variable global para evitar múltiples inicios del scheduler
_scheduler_initialized = False


class GmailAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gmail_app'

    def ready(self):
        """
        Se ejecuta cuando Django inicia
        Aquí iniciamos el scheduler para sincronización automática
        """
        global _scheduler_initialized

        from django.conf import settings

        # Evitar que StatReloader de Django inicie el scheduler múltiples veces
        # Solo iniciar si:
        # 1. No ha sido inicializado aún
        # 2. No estamos en el proceso reloader de Django
        if _scheduler_initialized:
            return

        # Verificar si estamos en el proceso main (no en reloader)
        if os.environ.get('RUN_MAIN') != 'true':
            return

        # Solo iniciar el scheduler si está configurado
        if getattr(settings, 'SCHEDULER_AUTOSTART', False):
            self.start_scheduler()
            _scheduler_initialized = True

    def start_scheduler(self):
        """Inicia el scheduler de APScheduler"""
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.interval import IntervalTrigger
            from django_apscheduler.jobstores import DjangoJobStore
            from django.conf import settings
            import atexit

            # Crear scheduler
            scheduler = BackgroundScheduler()
            scheduler.add_jobstore(DjangoJobStore(), "default")

            # Obtener intervalo de configuración
            interval_minutes = getattr(settings, 'AUTO_SYNC_INTERVAL_MINUTES', 20)

            # Agregar el job al scheduler con referencia textual
            scheduler.add_job(
                'gmail_app.scheduler:auto_sync_job',  # Referencia textual para serialización
                trigger=IntervalTrigger(minutes=interval_minutes),
                id='auto_sync_emails',
                name='Sincronización automática de emails',
                replace_existing=True,
            )

            # Iniciar el scheduler
            scheduler.start()
            logger.info(
                f'Scheduler iniciado - Sincronizacion automatica cada {interval_minutes} minutos'
            )

            # Detener el scheduler cuando Django se cierre
            atexit.register(lambda: scheduler.shutdown())

        except Exception as e:
            logger.error(f'Error iniciando scheduler: {e}')
            # No fallar el inicio de Django si el scheduler falla
            pass