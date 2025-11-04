"""
Comando de management para sincronizar emails automáticamente
Se ejecuta periódicamente mediante APScheduler
"""
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from gmail_app.models import GmailAccount, Email
from gmail_app.gmail_service import GmailService
from gmail_app.ai_service import EmailAIProcessor
from gmail_app.ai_models import AIContext
from gmail_app.exceptions import RefreshTokenInvalidError, GmailAPIError

logger = logging.getLogger('gmail_app')


class Command(BaseCommand):
    help = 'Sincroniza emails automáticamente para todos los usuarios con cuentas Gmail conectadas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Sincronizar solo para un usuario específico (username)',
        )

    def handle(self, *args, **options):
        username = options.get('user')

        if username:
            # Sincronizar solo para un usuario específico
            try:
                user = User.objects.get(username=username)
                self.sync_user_emails(user)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Usuario "{username}" no encontrado'))
        else:
            # Sincronizar para todos los usuarios con Gmail conectado
            gmail_accounts = GmailAccount.objects.select_related('user').all()

            if not gmail_accounts:
                self.stdout.write(self.style.WARNING('No hay cuentas Gmail conectadas'))
                return

            self.stdout.write(f'Sincronizando {gmail_accounts.count()} cuentas...')

            success_count = 0
            error_count = 0

            for gmail_account in gmail_accounts:
                try:
                    self.sync_user_emails(gmail_account.user)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f'Error al sincronizar {gmail_account.user.username}: {e}')

            self.stdout.write(
                self.style.SUCCESS(
                    f'Sincronización completada: {success_count} exitosas, {error_count} errores'
                )
            )

    def sync_user_emails(self, user):
        """Sincroniza emails para un usuario específico"""
        try:
            gmail_service = GmailService(user)
            synced_emails = gmail_service.sync_emails()

            if not synced_emails:
                self.stdout.write(f'  [{user.username}] No hay emails nuevos')
                return

            self.stdout.write(
                self.style.SUCCESS(
                    f'  [{user.username}] {len(synced_emails)} emails sincronizados'
                )
            )

            # Procesar con IA si está configurado
            try:
                ai_context = AIContext.objects.get(user=user, is_active=True)
                ai_processor = EmailAIProcessor()

                processed_count = 0
                responses_generated = 0
                auto_sent = 0

                for email in synced_emails:
                    try:
                        intent, ai_response = ai_processor.process_email(email)
                        processed_count += 1

                        if ai_response:
                            responses_generated += 1

                            # Auto-enviar si está configurado
                            if ai_context.auto_send and ai_response.status == 'pending_approval':
                                try:
                                    # Enviar el email automáticamente
                                    sent_message_id = gmail_service.send_email(
                                        to_email=ai_response.email_intent.email.sender,
                                        subject=ai_response.response_subject,
                                        body=ai_response.response_text,
                                        reply_to_message_id=ai_response.email_intent.email.gmail_id
                                    )

                                    # Marcar como enviado
                                    ai_response.status = 'sent'
                                    ai_response.sent_at = timezone.now()
                                    ai_response.save()

                                    auto_sent += 1
                                    logger.info(
                                        f'Auto-enviado: {ai_response.response_subject[:50]} a {email.sender}'
                                    )
                                except Exception as e:
                                    logger.error(f'Error auto-enviando email {email.id}: {e}')
                                    # Dejar como approved si falla el envío
                                    ai_response.status = 'approved'
                                    ai_response.save()

                    except Exception as e:
                        logger.error(f'Error procesando email {email.id}: {e}')

                if responses_generated > 0:
                    self.stdout.write(
                        f'    ├─ IA procesó {processed_count} emails'
                    )
                    self.stdout.write(
                        f'    ├─ {responses_generated} respuestas generadas'
                    )
                    if auto_sent > 0:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'    └─ ✉️  {auto_sent} respuestas AUTO-ENVIADAS'
                            )
                        )
                    else:
                        self.stdout.write(
                            f'    └─ 0 auto-enviadas (pendientes de aprobación)'
                        )

            except AIContext.DoesNotExist:
                # Usuario no tiene IA configurada
                pass

        except RefreshTokenInvalidError as e:
            self.stdout.write(
                self.style.ERROR(
                    f'  [{user.username}] Token expirado - Se requiere reconexión'
                )
            )
            # Eliminar cuenta para forzar reconexión
            try:
                GmailAccount.objects.get(user=user).delete()
            except GmailAccount.DoesNotExist:
                pass

        except GmailAPIError as e:
            self.stdout.write(
                self.style.ERROR(f'  [{user.username}] Error de API: {str(e)}')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  [{user.username}] Error inesperado: {str(e)}')
            )
            logger.exception(f'Error sincronizando para {user.username}')
