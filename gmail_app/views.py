import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from .gmail_service import GmailService
from .outlook_service import OutlookService
from .models import Email, EmailAccount, GmailAccount
from .exceptions import (
    RefreshTokenInvalidError, OAuthError, GmailAPIError,
    QuotaExceededError, PermissionError
)
from .ai_models import AIContext, TemporalRule, EmailIntent, AIResponse
from .ai_service import EmailAIProcessor
from .forms import UserRegistrationForm, UserLoginForm

logger = logging.getLogger('gmail_app')


def home(request):
    """Vista principal - redirige según estado de autenticación"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


def user_register(request):
    """Vista de registro de usuarios"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Iniciar sesión automáticamente después del registro
            login(request, user)
            messages.success(
                request,
                f'¡Bienvenido {user.username}! Tu cuenta ha sido creada exitosamente.'
            )
            logger.info(f"Nuevo usuario registrado: {user.username} ({user.email})")
            return redirect('dashboard')
        else:
            # Los errores del formulario se mostrarán automáticamente en el template
            logger.warning(f"Intento de registro fallido: {form.errors}")
    else:
        form = UserRegistrationForm()

    return render(request, 'gmail_app/register.html', {'form': form})


def user_login(request):
    """Vista de inicio de sesión"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido de vuelta, {user.username}!')
                logger.info(f"Usuario {user.username} inició sesión")

                # Redirigir a la página solicitada o al dashboard
                next_page = request.GET.get('next', 'dashboard')
                return redirect(next_page)
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
                logger.warning(f"Intento de login fallido para usuario: {username}")
        else:
            # Los errores del formulario se mostrarán automáticamente
            logger.warning(f"Formulario de login inválido: {form.errors}")
    else:
        form = UserLoginForm()

    return render(request, 'gmail_app/login.html', {'form': form})


@login_required
def user_logout(request):
    """Vista de cierre de sesión"""
    username = request.user.username
    logout(request)
    messages.success(request, f'Has cerrado sesión exitosamente. ¡Hasta pronto, {username}!')
    logger.info(f"Usuario {username} cerró sesión")
    return redirect('login')


@login_required
def dashboard(request):
    """
    Unified dashboard showing emails from ALL connected accounts
    (Gmail + Outlook), sorted chronologically
    """
    # Get all active email accounts for this user
    email_accounts = EmailAccount.objects.filter(user=request.user, is_active=True)

    # Get accounts by provider
    gmail_accounts = email_accounts.filter(provider='gmail')
    outlook_accounts = email_accounts.filter(provider='outlook')

    # Get last 50 emails from ALL accounts, unified and sorted by received_date
    if email_accounts.exists():
        emails = Email.objects.filter(
            email_account__in=email_accounts
        ).select_related('email_account').order_by('-received_date')[:50]
    else:
        # Fallback: check legacy GmailAccount
        try:
            legacy_gmail = GmailAccount.objects.get(user=request.user)
            emails = Email.objects.filter(gmail_account=legacy_gmail)[:20]
            has_legacy = True
        except GmailAccount.DoesNotExist:
            emails = []
            has_legacy = False

        context = {
            'emails': emails,
            'email_accounts': [],
            'gmail_accounts': [],
            'outlook_accounts': [],
            'has_accounts': False,
            'has_legacy_gmail': has_legacy,
            'total_accounts': 0
        }
        return render(request, 'gmail_app/dashboard.html', context)

    # Add sync statistics for each account
    accounts_with_stats = []
    for account in email_accounts:
        # Get email count for this account
        email_count = Email.objects.filter(email_account=account).count()

        # Get last synced email (most recent email from this account)
        last_email = Email.objects.filter(email_account=account).order_by('-received_date').first()
        last_sync_date = last_email.received_date if last_email else None

        accounts_with_stats.append({
            'account': account,
            'email_count': email_count,
            'last_sync_date': last_sync_date
        })

    context = {
        'emails': emails,
        'email_accounts': email_accounts,
        'accounts_with_stats': accounts_with_stats,
        'gmail_accounts': gmail_accounts,
        'outlook_accounts': outlook_accounts,
        'has_accounts': True,
        'has_gmail': gmail_accounts.exists(),
        'has_outlook': outlook_accounts.exists(),
        'total_accounts': email_accounts.count(),
        'total_emails': emails.count()
    }

    return render(request, 'gmail_app/dashboard.html', context)


@login_required
def connect_gmail(request):
    gmail_service = GmailService(request.user)
    authorization_url = gmail_service.get_authorization_url(request)
    return redirect(authorization_url)


@login_required
def gmail_callback(request):
    try:
        logger.info(f"Processing OAuth callback for user {request.user.username}")
        gmail_service = GmailService(request.user)
        gmail_account = gmail_service.handle_oauth_callback(request)
        messages.success(request, f'✅ Gmail account {gmail_account.email} connected successfully!')
        messages.info(request, '📥 Ready to sync your emails! Click "Sync Now" to start.')
        return redirect('dashboard')
    except OAuthError as e:
        logger.error(f"OAuth error for user {request.user.username}: {e}")
        if hasattr(e, 'error_type') and e.error_type == 'no_refresh_token':
            messages.error(
                request,
                '🔑 Please revoke existing permissions first:<br>'
                '1. Go to <a href="https://myaccount.google.com/permissions" target="_blank">Google Account Permissions</a><br>'
                '2. Find "FriendlyMail" and remove it<br>'
                '3. Come back and connect again<br><br>'
                f'Technical details: {str(e)}',
                extra_tags='oauth_error no_refresh_token'
            )
        else:
            messages.error(
                request, 
                f'🔐 Authentication error: {str(e)}. Please try connecting again.',
                extra_tags='oauth_error'
            )
        return redirect('dashboard')
    except Exception as e:
        logger.error(f"Unexpected error during OAuth callback for user {request.user.username}: {e}")
        error_str = str(e)
        
        if 'Scope has changed' in error_str:
            messages.error(
                request,
                '🔄 OAuth scopes have changed. Please:<br>'
                '1. <a href="/clear-oauth-session/" style="color: #1a73e8;">Clear OAuth session</a><br>'
                '2. Try connecting again<br><br>'
                'If this persists, revoke permissions in your Google account first.',
                extra_tags='scope_changed'
            )
        else:
            messages.error(
                request, 
                f'❌ Error connecting to Gmail: {error_str}. Please try again.',
                extra_tags='connection_error'
            )
        return redirect('dashboard')


@login_required
def sync_emails(request):
    """Show syncing page with progress"""
    return render(request, 'gmail_app/syncing.html')


@login_required
def sync_emails_api(request):
    """API endpoint for email synchronization"""
    try:
        logger.info(f"User {request.user.username} initiated email sync")
        gmail_service = GmailService(request.user)
        synced_emails = gmail_service.sync_emails()

        # Check if user has AI processing enabled
        try:
            ai_context = AIContext.objects.get(user=request.user, is_active=True)

            if synced_emails:
                # Process new emails with AI
                ai_processor = EmailAIProcessor()
                processed_count = 0
                responses_generated = 0

                for email in synced_emails:
                    try:
                        intent, ai_response = ai_processor.process_email(email)
                        processed_count += 1

                        if ai_response:
                            responses_generated += 1

                    except Exception as e:
                        logger.error(f"Error processing email {email.id} with AI: {e}")

                return JsonResponse({
                    'success': True,
                    'synced': len(synced_emails),
                    'ai_processed': processed_count,
                    'ai_responses': responses_generated,
                    'message': f'✅ Synced {len(synced_emails)} emails successfully!',
                    'ai_enabled': True
                })
            else:
                return JsonResponse({
                    'success': True,
                    'synced': 0,
                    'message': '✅ No new emails to sync',
                    'ai_enabled': True
                })

        except AIContext.DoesNotExist:
            return JsonResponse({
                'success': True,
                'synced': len(synced_emails),
                'message': f'✅ Synced {len(synced_emails)} new emails successfully!',
                'ai_enabled': False
            })

    except RefreshTokenInvalidError as e:
        logger.warning(f"Token expired for user {request.user.username}: {e}")
        # Delete the expired account to force reconnection
        try:
            GmailAccount.objects.get(user=request.user).delete()
        except GmailAccount.DoesNotExist:
            pass
        return JsonResponse({
            'success': False,
            'error': 'token_expired',
            'message': '⚠️ Your Gmail access has expired. Please reconnect your account.'
        })
    except QuotaExceededError as e:
        logger.error(f"Gmail API quota exceeded for user {request.user.username}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'quota_exceeded',
            'message': '⏳ Gmail API quota exceeded. Please try again in a few minutes.'
        })
    except PermissionError as e:
        logger.error(f"Permission error for user {request.user.username}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'permission_error',
            'message': '🔒 Insufficient permissions. Please reconnect your account.'
        })
    except GmailAPIError as e:
        logger.error(f"Gmail API error for user {request.user.username}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'api_error',
            'message': f'📧 Gmail service error: {str(e)}. Please try again later.'
        })
    except Exception as e:
        logger.error(f"Unexpected error during sync for user {request.user.username}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'unexpected_error',
            'message': f'❌ Unexpected error occurred: {str(e)}.'
        })


@login_required
def email_detail(request, email_id):
    try:
        email = Email.objects.get(id=email_id, gmail_account__user=request.user)
        return render(request, 'gmail_app/email_detail.html', {'email': email})
    except Email.DoesNotExist:
        messages.error(request, 'Email not found')
        return redirect('dashboard')


@login_required
def system_logs(request):
    """Display system logs for debugging"""
    try:
        with open('logs/app.log', 'r') as f:
            logs = f.readlines()[-100:]  # Last 100 lines
        return JsonResponse({
            'success': True,
            'logs': logs
        })
    except FileNotFoundError:
        return JsonResponse({
            'success': False,
            'error': 'Log file not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def disconnect_gmail(request):
    """Disconnect Gmail account"""
    try:
        gmail_account = GmailAccount.objects.get(user=request.user)
        email = gmail_account.email
        
        # Delete all associated emails first
        Email.objects.filter(gmail_account=gmail_account).delete()
        
        # Delete the Gmail account
        gmail_account.delete()
        
        logger.info(f"User {request.user.username} disconnected Gmail account {email}")
        messages.success(request, f'✅ Successfully disconnected Gmail account {email}')
        
    except GmailAccount.DoesNotExist:
        messages.warning(request, '⚠️ No Gmail account found to disconnect')
    except Exception as e:
        logger.error(f"Error disconnecting Gmail for user {request.user.username}: {e}")
        messages.error(request, f'❌ Error disconnecting Gmail: {str(e)}')
    
    return redirect('dashboard')


@login_required
def clear_oauth_session(request):
    """Clear OAuth session data"""
    try:
        # Clear OAuth-related session data
        oauth_keys = ['oauth_state', 'oauth_flow', 'credentials']
        cleared_keys = []
        
        for key in oauth_keys:
            if key in request.session:
                del request.session[key]
                cleared_keys.append(key)
        
        # Force session save
        request.session.modified = True
        
        if cleared_keys:
            logger.info(f"Cleared OAuth session keys for user {request.user.username}: {cleared_keys}")
            messages.success(request, f'✅ OAuth session cleared. Keys removed: {", ".join(cleared_keys)}')
        else:
            messages.info(request, 'ℹ️ No OAuth session data found to clear')
            
    except Exception as e:
        logger.error(f"Error clearing OAuth session for user {request.user.username}: {e}")
        messages.error(request, f'❌ Error clearing session: {str(e)}')
    
    return redirect('dashboard')


@login_required
def ai_config(request):
    """Configure AI context and rules"""
    try:
        ai_context = AIContext.objects.get(user=request.user)
    except AIContext.DoesNotExist:
        ai_context = None
    
    # Get user's temporal rules
    temporal_rules = TemporalRule.objects.filter(
        ai_context__user=request.user
    ).order_by('-priority', '-created_at') if ai_context else []
    
    context = {
        'ai_context': ai_context,
        'temporal_rules': temporal_rules,
        'has_ai_config': ai_context is not None
    }

    return render(request, 'gmail_app/ai_config_simple.html', context)


@login_required
def ai_context_save(request):
    """Save or update AI context"""
    if request.method == 'POST':
        try:
            # Get or create AI context
            ai_context, created = AIContext.objects.get_or_create(
                user=request.user,
                defaults={'role': 'Assistant', 'context_description': ''}
            )
            
            # Update fields
            ai_context.role = request.POST.get('role', '')
            ai_context.context_description = request.POST.get('context_description', '')
            ai_context.complexity_level = request.POST.get('complexity_level', 'simple')
            ai_context.can_respond_topics = request.POST.get('can_respond_topics', '')
            ai_context.cannot_respond_topics = request.POST.get('cannot_respond_topics', '')
            ai_context.allowed_domains = request.POST.get('allowed_domains', '')
            ai_context.auto_send = request.POST.get('auto_send') == 'on'
            ai_context.is_active = request.POST.get('is_active') == 'on'
            
            ai_context.save()
            
            action = 'created' if created else 'updated'
            messages.success(request, f'🤖 AI context {action} successfully!')
            logger.info(f"AI context {action} for user {request.user.username}")
            
        except Exception as e:
            logger.error(f"Error saving AI context for user {request.user.username}: {e}")
            messages.error(request, f'❌ Error saving AI context: {str(e)}')
    
    return redirect('ai_config')


@login_required 
def temporal_rule_save(request):
    """Save or update temporal rule"""
    if request.method == 'POST':
        try:
            # Get user's AI context
            ai_context = AIContext.objects.get(user=request.user)
            
            rule_id = request.POST.get('rule_id')
            
            if rule_id:
                # Update existing rule
                rule = TemporalRule.objects.get(id=rule_id, ai_context=ai_context)
                action = 'updated'
            else:
                # Create new rule
                rule = TemporalRule(ai_context=ai_context)
                action = 'created'
            
            # Update fields
            rule.name = request.POST.get('name', '')
            rule.description = request.POST.get('description', '')
            rule.start_date = request.POST.get('start_date')
            rule.end_date = request.POST.get('end_date')
            rule.keywords = request.POST.get('keywords', '')
            rule.email_filters = request.POST.get('email_filters', '')
            rule.response_template = request.POST.get('response_template', '')
            rule.status = request.POST.get('status', 'draft')
            rule.priority = int(request.POST.get('priority', 1))
            
            rule.save()
            
            messages.success(request, f'⏰ Temporal rule "{rule.name}" {action} successfully!')
            logger.info(f"Temporal rule {action} by user {request.user.username}: {rule.name}")
            
        except AIContext.DoesNotExist:
            messages.error(request, '⚠️ Please configure your AI context first')
        except Exception as e:
            logger.error(f"Error saving temporal rule for user {request.user.username}: {e}")
            messages.error(request, f'❌ Error saving rule: {str(e)}')
    
    return redirect('ai_config')


@login_required
def temporal_rule_delete(request, rule_id):
    """Delete temporal rule"""
    try:
        rule = TemporalRule.objects.get(
            id=rule_id, 
            ai_context__user=request.user
        )
        rule_name = rule.name
        rule.delete()
        
        messages.success(request, f'🗑️ Rule "{rule_name}" deleted successfully')
        logger.info(f"Temporal rule deleted by user {request.user.username}: {rule_name}")
        
    except TemporalRule.DoesNotExist:
        messages.error(request, '❌ Rule not found')
    except Exception as e:
        logger.error(f"Error deleting temporal rule for user {request.user.username}: {e}")
        messages.error(request, f'❌ Error deleting rule: {str(e)}')
    
    return redirect('ai_config')


@login_required
def ai_responses(request):
    """View and manage AI responses"""
    try:
        ai_context = AIContext.objects.get(user=request.user)

        # Get pending responses
        pending_responses = AIResponse.objects.filter(
            email_intent__email__gmail_account__user=request.user,
            status='pending_approval'
        ).select_related('email_intent__email').order_by('-generated_at')

        # Get sent responses
        sent_responses = AIResponse.objects.filter(
            email_intent__email__gmail_account__user=request.user,
            status='sent'
        ).select_related('email_intent__email').order_by('-sent_at')[:50]

        # Get approved but not sent responses
        approved_responses = AIResponse.objects.filter(
            email_intent__email__gmail_account__user=request.user,
            status='approved'
        ).select_related('email_intent__email').order_by('-approved_at')

        # Get rejected responses
        rejected_responses = AIResponse.objects.filter(
            email_intent__email__gmail_account__user=request.user,
            status='rejected'
        ).select_related('email_intent__email').order_by('-generated_at')[:20]

        context = {
            'ai_context': ai_context,
            'pending_responses': pending_responses,
            'sent_responses': sent_responses,
            'approved_responses': approved_responses,
            'rejected_responses': rejected_responses,
            'has_pending': pending_responses.exists(),
            'has_sent': sent_responses.exists(),
            'has_ai_config': True
        }

    except AIContext.DoesNotExist:
        context = {
            'has_ai_config': False,
            'ai_context': None,
            'pending_responses': [],
            'sent_responses': [],
            'approved_responses': [],
            'rejected_responses': [],
            'has_pending': False,
            'has_sent': False
        }

    return render(request, 'gmail_app/ai_responses.html', context)


@login_required
def approve_response(request, response_id):
    """Approve and send AI response (allows retry for approved responses)"""
    try:
        # Accept both 'pending_approval' and 'approved' to allow retries
        ai_response = AIResponse.objects.get(
            id=response_id,
            email_intent__email__gmail_account__user=request.user
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
            id=response_id,
            email_intent__email__gmail_account__user=request.user,
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
        ai_response = AIResponse.objects.get(
            id=response_id,
            email_intent__email__gmail_account__user=request.user
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
def process_existing_emails(request):
    """Process existing emails with AI"""
    try:
        ai_context = AIContext.objects.get(user=request.user, is_active=True)
        
        # Get emails that haven't been processed by AI yet
        unprocessed_emails = Email.objects.filter(
            gmail_account__user=request.user
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
            
    except AIContext.DoesNotExist:
        messages.error(request, '⚠️ Please configure your AI context first.')
        return redirect('ai_config')
    except Exception as e:
        logger.error(f"Error processing existing emails for user {request.user.username}: {e}")
        messages.error(request, f'❌ Error processing emails: {str(e)}')
    
    return redirect('ai_responses')


@login_required
def debug_ai_status(request):
    """Debug AI configuration and status"""
    try:
        # Check AI Context
        try:
            ai_context = AIContext.objects.get(user=request.user)
            ai_context_info = {
                'exists': True,
                'is_active': ai_context.is_active,
                'role': ai_context.role,
                'has_description': bool(ai_context.context_description),
                'complexity_level': ai_context.complexity_level,
                'auto_send': ai_context.auto_send,
            }
        except AIContext.DoesNotExist:
            ai_context_info = {'exists': False}

        # Check Gmail connection
        try:
            gmail_account = GmailAccount.objects.get(user=request.user)
            gmail_info = {
                'connected': True,
                'email': gmail_account.email,
                'has_refresh_token': bool(gmail_account.refresh_token),
            }
        except GmailAccount.DoesNotExist:
            gmail_info = {'connected': False}

        # Check emails
        total_emails = Email.objects.filter(gmail_account__user=request.user).count()
        processed_emails = EmailIntent.objects.filter(email__gmail_account__user=request.user).count()

        # Check responses by status
        pending_count = AIResponse.objects.filter(
            email_intent__email__gmail_account__user=request.user,
            status='pending_approval'
        ).count()

        sent_count = AIResponse.objects.filter(
            email_intent__email__gmail_account__user=request.user,
            status='sent'
        ).count()

        approved_count = AIResponse.objects.filter(
            email_intent__email__gmail_account__user=request.user,
            status='approved'
        ).count()

        rejected_count = AIResponse.objects.filter(
            email_intent__email__gmail_account__user=request.user,
            status='rejected'
        ).count()

        # Check temporal rules
        temporal_rules = TemporalRule.objects.filter(ai_context__user=request.user).count()

        # Check scheduler status
        from django.conf import settings
        scheduler_enabled = getattr(settings, 'SCHEDULER_AUTOSTART', False)
        sync_interval = getattr(settings, 'AUTO_SYNC_INTERVAL_MINUTES', 20)

        debug_info = {
            'ai_context': ai_context_info,
            'gmail': gmail_info,
            'emails': {
                'total': total_emails,
                'processed_by_ai': processed_emails,
                'unprocessed': total_emails - processed_emails
            },
            'responses': {
                'pending_approval': pending_count,
                'sent': sent_count,
                'approved_not_sent': approved_count,
                'rejected': rejected_count,
                'total': pending_count + sent_count + approved_count + rejected_count
            },
            'temporal_rules': temporal_rules,
            'openai_configured': bool(settings.OPENAI_API_KEY),
            'scheduler': {
                'enabled': scheduler_enabled,
                'interval_minutes': sync_interval
            },
            'auto_send_diagnosis': {
                'ai_context_exists': ai_context_info.get('exists', False),
                'ai_is_active': ai_context_info.get('is_active', False),
                'auto_send_enabled': ai_context_info.get('auto_send', False),
                'gmail_connected': gmail_info.get('connected', False),
                'scheduler_running': scheduler_enabled,
                'ready_to_auto_send': (
                    ai_context_info.get('exists', False) and
                    ai_context_info.get('is_active', False) and
                    ai_context_info.get('auto_send', False) and
                    gmail_info.get('connected', False) and
                    scheduler_enabled
                )
            }
        }

        return JsonResponse({
            'success': True,
            'debug_info': debug_info
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# ========== OUTLOOK/OFFICE 365 VIEWS ==========

@login_required
def connect_outlook(request):
    """Initiate Outlook OAuth2 flow"""
    try:
        outlook_service = OutlookService(request.user)
        authorization_url = outlook_service.get_authorization_url(request)
        logger.info(f"User {request.user.username} initiating Outlook connection")
        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"Error initiating Outlook connection for {request.user.username}: {e}")
        messages.error(request, f'❌ Error connecting to Outlook: {str(e)}')
        return redirect('dashboard')


@login_required
def outlook_callback(request):
    """Handle Outlook OAuth2 callback"""
    try:
        logger.info(f"Processing Outlook OAuth callback for user {request.user.username}")
        outlook_service = OutlookService(request.user)
        email_account = outlook_service.handle_oauth_callback(request)
        
        messages.success(
            request,
            f'✅ Outlook account {email_account.email} connected successfully!'
        )
        messages.info(request, '📥 Ready to sync your Outlook emails! Click "Sync Outlook" to start.')
        return redirect('dashboard')
        
    except Exception as e:
        logger.error(f"Outlook OAuth error for user {request.user.username}: {e}")
        error_str = str(e)
        
        if 'Invalid state parameter' in error_str:
            messages.error(
                request,
                '🔒 Security validation failed. Please try connecting again.',
                extra_tags='oauth_error'
            )
        elif 'No refresh token' in error_str:
            messages.error(
                request,
                '🔑 Refresh token not received. Please ensure you grant all permissions when prompted.',
                extra_tags='oauth_error'
            )
        else:
            messages.error(
                request,
                f'❌ Error connecting to Outlook: {error_str}. Please try again.',
                extra_tags='connection_error'
            )
        return redirect('dashboard')


@login_required
def sync_outlook(request):
    """Sync emails from Outlook"""
    try:
        logger.info(f"User {request.user.username} initiated Outlook email sync")
        outlook_service = OutlookService(request.user)
        result = outlook_service.sync_emails(max_results=50)
        
        messages.success(
            request,
            f'✅ Synced {result["total_synced"]} Outlook emails! '
            f'({result["new_emails"]} new, {result["updated_emails"]} updated)'
        )
        logger.info(
            f"Outlook sync complete for {request.user.username}: "
            f"{result['new_emails']} new, {result['updated_emails']} updated"
        )
        
    except Exception as e:
        logger.error(f"Outlook sync error for user {request.user.username}: {e}")
        error_str = str(e)
        
        if 'No active Outlook account' in error_str:
            messages.error(request, '⚠️ Please connect your Outlook account first.')
        elif 'Failed to refresh token' in error_str:
            messages.error(request, '🔑 Your Outlook access has expired. Please reconnect your account.')
        else:
            messages.error(request, f'📧 Error syncing Outlook emails: {error_str}')
    
    return redirect('dashboard')


@login_required
def disconnect_outlook(request, account_id):
    """Disconnect specific Outlook account"""
    try:
        account = EmailAccount.objects.get(
            id=account_id,
            user=request.user,
            provider='outlook'
        )
        email = account.email
        
        # Deactivate account (don't delete emails, just deactivate)
        account.is_active = False
        account.save()
        
        logger.info(f"User {request.user.username} disconnected Outlook account {email}")
        messages.success(request, f'✅ Successfully disconnected Outlook account {email}')
        
    except EmailAccount.DoesNotExist:
        messages.warning(request, '⚠️ Outlook account not found')
        logger.warning(f"User {request.user.username} tried to disconnect non-existent Outlook account {account_id}")
    except Exception as e:
        logger.error(f"Error disconnecting Outlook for user {request.user.username}: {e}")
        messages.error(request, f'❌ Error disconnecting Outlook: {str(e)}')
    
    return redirect('dashboard')


@login_required
def disconnect_email_account(request, account_id):
    """Disconnect any email account (Gmail or Outlook)"""
    try:
        account = EmailAccount.objects.get(
            id=account_id,
            user=request.user
        )
        email = account.email
        provider = account.get_provider_display()
        
        # Deactivate account
        account.is_active = False
        account.save()
        
        logger.info(f"User {request.user.username} disconnected {provider} account {email}")
        messages.success(request, f'✅ Successfully disconnected {provider} account {email}')
        
    except EmailAccount.DoesNotExist:
        messages.warning(request, '⚠️ Email account not found')
        logger.warning(f"User {request.user.username} tried to disconnect non-existent account {account_id}")
    except Exception as e:
        logger.error(f"Error disconnecting email account for user {request.user.username}: {e}")
        messages.error(request, f'❌ Error disconnecting account: {str(e)}')
    
    return redirect('dashboard')


@login_required
def sync_all_accounts(request):
    """Sync emails from ALL connected accounts (Gmail + Outlook)"""
    try:
        email_accounts = EmailAccount.objects.filter(user=request.user, is_active=True)
        
        if not email_accounts.exists():
            messages.warning(request, '⚠️ No email accounts connected. Please connect Gmail or Outlook first.')
            return redirect('dashboard')
        
        total_synced = 0
        total_new = 0
        total_updated = 0
        errors = []
        
        # Sync Gmail accounts
        gmail_accounts = email_accounts.filter(provider='gmail')
        for account in gmail_accounts:
            try:
                gmail_service = GmailService(request.user)
                # Note: GmailService needs to be updated to support multiple accounts
                # For now, this will only sync the first Gmail account
                synced_emails = gmail_service.sync_emails()
                count = len(synced_emails) if synced_emails else 0
                total_synced += count
                total_new += count
                logger.info(f"Synced {count} emails from Gmail account {account.email}")
            except Exception as e:
                error_msg = f"Gmail ({account.email}): {str(e)}"
                errors.append(error_msg)
                logger.error(f"Error syncing Gmail account {account.email}: {e}")
        
        # Sync Outlook accounts
        outlook_accounts = email_accounts.filter(provider='outlook')
        for account in outlook_accounts:
            try:
                outlook_service = OutlookService(request.user)
                result = outlook_service.sync_emails(max_results=50)
                total_synced += result['total_synced']
                total_new += result['new_emails']
                total_updated += result['updated_emails']
                logger.info(
                    f"Synced {result['total_synced']} emails from Outlook account {account.email}: "
                    f"{result['new_emails']} new, {result['updated_emails']} updated"
                )
            except Exception as e:
                error_msg = f"Outlook ({account.email}): {str(e)}"
                errors.append(error_msg)
                logger.error(f"Error syncing Outlook account {account.email}: {e}")
        
        # Show results
        if total_synced > 0:
            messages.success(
                request,
                f'✅ Synced {total_synced} emails from {email_accounts.count()} account(s)! '
                f'({total_new} new, {total_updated} updated)'
            )
        else:
            messages.info(request, 'ℹ️ No new emails to sync')
        
        if errors:
            for error in errors:
                messages.warning(request, f'⚠️ {error}')
        
        logger.info(
            f"Sync all complete for {request.user.username}: "
            f"{total_synced} total, {total_new} new, {total_updated} updated"
        )
        
    except Exception as e:
        logger.error(f"Error syncing all accounts for user {request.user.username}: {e}")
        messages.error(request, f'❌ Error syncing accounts: {str(e)}')
    
    return redirect('dashboard')
