"""
AI Response management views - View, approve, reject, resend AI-generated responses
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from ..models import Email, EmailAccount, GmailAccount
from ..ai_models import AIRole, EmailIntent, AIResponse
from ..ai_service import EmailAIProcessor
from ..gmail_service import GmailService

logger = logging.getLogger('gmail_app')


@login_required
def ai_responses(request):
    """View and manage AI responses"""
    try:
        # Get active AI role
        ai_role = AIRole.objects.get(user=request.user, is_active=True)
        has_ai_role = True

        # Build query to get responses from both email_account and gmail_account
        pending_responses = AIResponse.objects.filter(
            Q(email_intent__email__email_account__user=request.user) |
            Q(email_intent__email__gmail_account__user=request.user),
            status='pending_approval'
        ).select_related('email_intent__email').order_by('-generated_at')

        sent_responses = AIResponse.objects.filter(
            Q(email_intent__email__email_account__user=request.user) |
            Q(email_intent__email__gmail_account__user=request.user),
            status='sent'
        ).select_related('email_intent__email').order_by('-sent_at')[:50]

        approved_responses = AIResponse.objects.filter(
            Q(email_intent__email__email_account__user=request.user) |
            Q(email_intent__email__gmail_account__user=request.user),
            status='approved'
        ).select_related('email_intent__email').order_by('-approved_at')

        rejected_responses = AIResponse.objects.filter(
            Q(email_intent__email__email_account__user=request.user) |
            Q(email_intent__email__gmail_account__user=request.user),
            status='rejected'
        ).select_related('email_intent__email').order_by('-generated_at')[:20]

        # Calcular estadísticas para el resumen
        email_accounts = EmailAccount.objects.filter(user=request.user)
        gmail_accounts = GmailAccount.objects.filter(user=request.user)

        total_emails = Email.objects.filter(
            Q(email_account__in=email_accounts) | Q(gmail_account__in=gmail_accounts)
        ).count()

        responded_emails = EmailIntent.objects.filter(
            Q(email__email_account__in=email_accounts) |
            Q(email__gmail_account__in=gmail_accounts),
            airesponse__isnull=False
        ).distinct().count()

        context = {
            'ai_role': ai_role,
            'pending_responses': pending_responses,
            'sent_responses': sent_responses,
            'approved_responses': approved_responses,
            'rejected_responses': rejected_responses,
            'has_pending': pending_responses.exists(),
            'has_sent': sent_responses.exists(),
            'has_ai_role': True,
            'total_emails': total_emails,
            'responded_emails': responded_emails,
        }

    except AIRole.DoesNotExist:
        logger.warning(f"No active AI role for user {request.user.username}")
        context = {
            'has_ai_role': False,
            'ai_role': None,
            'pending_responses': [],
            'sent_responses': [],
            'approved_responses': [],
            'rejected_responses': [],
            'has_pending': False,
            'has_sent': False,
            'total_emails': 0,
            'responded_emails': 0,
        }

    except Exception as e:
        logger.error(f"Error in ai_responses for user {request.user.username}: {e}")
        context = {
            'has_ai_role': False,
            'ai_role': None,
            'pending_responses': [],
            'sent_responses': [],
            'approved_responses': [],
            'rejected_responses': [],
            'has_pending': False,
            'has_sent': False,
            'total_emails': 0,
            'responded_emails': 0,
            'error': str(e)
        }

    return render(request, 'gmail_app/ai_responses.html', context)


@login_required
def approve_response(request, response_id):
    """Approve and send AI response (allows retry for approved responses)"""
    try:
        # Accept both 'pending_approval' and 'approved' to allow retries
        # Support both email_account and gmail_account
        ai_response = AIResponse.objects.get(
            Q(email_intent__email__gmail_account__user=request.user) |
            Q(email_intent__email__email_account__user=request.user),
            id=response_id
        )

        # Only allow pending or approved (not sent or rejected)
        if ai_response.status not in ['pending_approval', 'approved']:
            messages.warning(
                request,
                f'Esta respuesta ya fue {ai_response.get_status_display()}. No se puede enviar de nuevo desde aqui.'
            )
            return redirect('ai_responses')

        logger.info(f"User {request.user.username} attempting to send response {response_id} (current status: {ai_response.status})")

        # Mark as approved first
        ai_response.status = 'approved'
        ai_response.approved_at = timezone.now()
        ai_response.save()

        # Try to send the email
        try:
            logger.info(f"Creating Gmail service for user {request.user.username}")
            gmail_service = GmailService(request.user)

            logger.info(f"Attempting to send email to {ai_response.email_intent.email.sender}")
            logger.info(f"  Subject: {ai_response.response_subject}")
            logger.info(f"  Reply to: {ai_response.email_intent.email.provider_id}")

            sent_message_id = gmail_service.send_email(
                to_email=ai_response.email_intent.email.sender,
                subject=ai_response.response_subject,
                body=ai_response.response_text,
                reply_to_message_id=ai_response.email_intent.email.provider_id
            )

            logger.info(f"Email sent successfully! Message ID: {sent_message_id}")

            # Update status to sent
            ai_response.status = 'sent'
            ai_response.sent_at = timezone.now()
            ai_response.save()

            messages.success(request, f'Correo enviado exitosamente a {ai_response.email_intent.email.sender}!')
            logger.info(f"Email sent by user {request.user.username} to {ai_response.email_intent.email.sender}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"ERROR enviando email (response {response_id}): {error_msg}")
            logger.exception("Stack trace completo:")  # Esto imprime el stack trace completo

            messages.error(
                request,
                f'Error al enviar email: {error_msg}. La respuesta queda aprobada pero no enviada. Puedes intentar reenviarla desde el tab "Aprobadas".'
            )

            # Keep as approved but not sent
            ai_response.status = 'approved'
            ai_response.save()

    except AIResponse.DoesNotExist:
        messages.error(request, 'Respuesta no encontrada o no tienes permiso para acceder a ella')
        logger.warning(f"User {request.user.username} tried to approve non-existent response {response_id}")
    except Exception as e:
        logger.error(f"Error inesperado aprobando respuesta: {e}")
        logger.exception("Stack trace:")
        messages.error(request, f'Error inesperado: {str(e)}')

    return redirect('ai_responses')


@login_required
def reject_response(request, response_id):
    """Reject AI response"""
    try:
        ai_response = AIResponse.objects.get(
            Q(email_intent__email__gmail_account__user=request.user) |
            Q(email_intent__email__email_account__user=request.user),
            id=response_id,
            status='pending_approval'
        )

        ai_response.status = 'rejected'
        if request.POST.get('feedback'):
            ai_response.user_feedback = request.POST.get('feedback')
        ai_response.save()

        messages.warning(request, f'❌ Response rejected. Email will require manual response.')
        logger.info(f"Response rejected by user {request.user.username}: {response_id}")

    except AIResponse.DoesNotExist:
        messages.error(request, '❌ Response not found or already processed')
    except Exception as e:
        logger.error(f"Error rejecting response for user {request.user.username}: {e}")
        messages.error(request, f'❌ Error rejecting response: {str(e)}')

    return redirect('ai_responses')


@login_required
def resend_response(request, response_id):
    """Resend or send a previously sent/approved AI response"""
    try:
        # Accept both 'sent' and 'approved' statuses
        # Support both email_account and gmail_account
        ai_response = AIResponse.objects.get(
            Q(email_intent__email__gmail_account__user=request.user) |
            Q(email_intent__email__email_account__user=request.user),
            id=response_id
        )

        # Only allow resending for 'sent' or 'approved' responses
        if ai_response.status not in ['sent', 'approved']:
            messages.warning(
                request,
                f'⚠️ Solo puedes reenviar respuestas que fueron enviadas o aprobadas. Estado actual: {ai_response.get_status_display()}'
            )
            return redirect('ai_responses')

        # Send the email
        try:
            logger.info(f"User {request.user.username} attempting to resend response {response_id} with status {ai_response.status}")

            gmail_service = GmailService(request.user)
            sent_message_id = gmail_service.send_email(
                to_email=ai_response.email_intent.email.sender,
                subject=ai_response.response_subject,
                body=ai_response.response_text,
                reply_to_message_id=ai_response.email_intent.email.provider_id
            )

            # Update status and timestamp
            ai_response.status = 'sent'
            ai_response.sent_at = timezone.now()
            ai_response.save()

            messages.success(request, f'📧 Respuesta enviada exitosamente a {ai_response.email_intent.email.sender}!')
            logger.info(f"Email resent by user {request.user.username} to {ai_response.email_intent.email.sender}")

        except Exception as e:
            logger.error(f"Error resending response {response_id}: {e}")
            messages.error(request, f'❌ Error al enviar email: {str(e)}. Por favor verifica tu conexión con Gmail.')

    except AIResponse.DoesNotExist:
        messages.error(request, '❌ Respuesta no encontrada o no tienes permiso para acceder a ella')
        logger.warning(f"User {request.user.username} tried to resend non-existent response {response_id}")
    except Exception as e:
        logger.error(f"Unexpected error in resend_response for user {request.user.username}: {e}")
        messages.error(request, f'❌ Error inesperado al reenviar: {str(e)}')

    return redirect('ai_responses')


@login_required
def edit_response(request, response_id):
    """Edit AI response before sending"""
    try:
        # Support both email_account and gmail_account
        ai_response = AIResponse.objects.get(
            id=response_id,
            status__in=['pending_approval', 'approved']
        )

        # Verify user ownership
        email = ai_response.email_intent.email
        if not (email.email_account and email.email_account.user == request.user) and \
           not (email.gmail_account and email.gmail_account.user == request.user):
            messages.error(request, '❌ No tienes permiso para editar esta respuesta')
            return redirect('ai_responses')

        if request.method == 'POST':
            # Update response text and subject
            ai_response.response_text = request.POST.get('response_text', ai_response.response_text)
            ai_response.response_subject = request.POST.get('response_subject', ai_response.response_subject)
            ai_response.save()

            messages.success(request, '✅ Respuesta actualizada correctamente')
            logger.info(f"Response {response_id} edited by user {request.user.username}")
            return redirect('ai_responses')

        context = {
            'ai_response': ai_response,
            'email': ai_response.email_intent.email,
        }
        return render(request, 'gmail_app/edit_response.html', context)

    except AIResponse.DoesNotExist:
        messages.error(request, '❌ Respuesta no encontrada o no disponible para editar')
    except Exception as e:
        logger.error(f"Error editing response {response_id} for user {request.user.username}: {e}")
        messages.error(request, f'❌ Error: {str(e)}')

    return redirect('ai_responses')


@login_required
def process_existing_emails(request):
    """Process existing emails with AI"""
    try:
        # Get active AIRole
        ai_role = AIRole.objects.get(user=request.user, is_active=True)

        # Get emails that haven't been processed by AI yet
        unprocessed_emails = Email.objects.filter(
            Q(email_account__user=request.user) | Q(gmail_account__user=request.user)
        ).exclude(
            id__in=EmailIntent.objects.values('email_id')
        )[:10]  # Process max 10 emails at once to avoid timeout

        if not unprocessed_emails:
            messages.info(request, 'ℹ️ No unprocessed emails found. All emails have been analyzed by AI.')
            return redirect('ai_responses')

        ai_processor = EmailAIProcessor()
        processed_count = 0
        responses_generated = 0

        logger.info(f"Processing {len(unprocessed_emails)} existing emails for user {request.user.username}")

        for email in unprocessed_emails:
            try:
                intent, ai_response = ai_processor.process_email(email)
                processed_count += 1

                if ai_response:
                    responses_generated += 1

            except Exception as e:
                logger.error(f"Error processing existing email {email.id} with AI: {e}")

        if responses_generated > 0:
            messages.success(request,
                f'🤖 Processed {processed_count} existing emails! AI generated {responses_generated} responses.')
            messages.info(request,
                f'📤 {responses_generated} responses are pending your approval.')
        else:
            messages.success(request,
                f'🤖 Analyzed {processed_count} existing emails. None required responses.')

        if len(unprocessed_emails) == 10:
            messages.info(request,
                f'💡 There might be more emails to process. Click "Process More" to continue.')

    except AIRole.DoesNotExist:
        messages.error(request, '⚠️ Please create an active AI role first.')
        return redirect('ai_roles_list')
    except Exception as e:
        logger.error(f"Error processing existing emails for user {request.user.username}: {e}")
        messages.error(request, f'❌ Error processing emails: {str(e)}')

    return redirect('ai_responses')
