"""
Módulo para funciones del scheduler
Separado de apps.py para permitir serialización
"""
import logging
from django.core.management import call_command

logger = logging.getLogger('gmail_app')


def auto_sync_job():
    """Job que ejecuta la sincronización automática"""
    logger.info('⏰ Iniciando sincronización automática...')
    try:
        call_command('auto_sync_emails')
        logger.info('✅ Sincronización automática completada')
    except Exception as e:
        logger.error(f'❌ Error en sincronización automática: {e}')
