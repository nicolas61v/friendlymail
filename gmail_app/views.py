import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from .gmail_service import GmailService
from .models import Email, GmailAccount
from .exceptions import (
    RefreshTokenInvalidError, OAuthError, GmailAPIError, 
    QuotaExceededError, PermissionError
)
from .ai_models import AIContext, TemporalRule, EmailIntent, AIResponse
from .ai_service import EmailAIProcessor

logger = logging.getLogger('gmail_app')


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'gmail_app/home.html')


def simple_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', 'testuser')
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password('testpass123')
            user.save()
        login(request, user)
        return redirect('dashboard')
    return render(request, 'gmail_app/login.html')


@login_required
def dashboard(request):
    try:
        gmail_account = GmailAccount.objects.get(user=request.user)
        emails = Email.objects.filter(gmail_account=gmail_account)[:20]
        context = {
            'gmail_account': gmail_account,
            'emails': emails,
            'has_gmail': True
        }
    except GmailAccount.DoesNotExist:
        context = {
            'has_gmail': False
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
        return redirect('sync_emails')
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
                
                if responses_generated > 0:
                    messages.success(request, 
                        f'✅ Synced {len(synced_emails)} emails, AI generated {responses_generated} responses!')
                    messages.info(request, 
                        f'🤖 {responses_generated} AI responses pending your approval. <a href="/ai-responses/">Review them here</a>')
                else:
                    messages.success(request, 
                        f'✅ Synced {len(synced_emails)} emails, {processed_count} analyzed by AI')
            else:
                messages.success(request, f'✅ Synced {len(synced_emails)} new emails successfully!')
                
        except AIContext.DoesNotExist:
            messages.success(request, f'✅ Synced {len(synced_emails)} new emails successfully!')
            if synced_emails:
                messages.info(request, 
                    f'💡 <a href="/ai-config/">Configure AI Assistant</a> to automatically analyze and respond to emails')
    except RefreshTokenInvalidError as e:
        logger.warning(f"Token expired for user {request.user.username}: {e}")
        messages.error(
            request, 
            '⚠️ Your Gmail access has expired. Please reconnect your account to continue syncing emails.',
            extra_tags='oauth_expired'
        )
        # Delete the expired account to force reconnection
        try:
            GmailAccount.objects.get(user=request.user).delete()
        except GmailAccount.DoesNotExist:
            pass
    except QuotaExceededError as e:
        logger.error(f"Gmail API quota exceeded for user {request.user.username}: {e}")
        messages.error(
            request,
            '⏳ Gmail API quota exceeded. Please try again in a few minutes.',
            extra_tags='quota_exceeded'
        )
    except PermissionError as e:
        logger.error(f"Permission error for user {request.user.username}: {e}")
        messages.error(
            request,
            '🔒 Insufficient permissions to access Gmail. Please reconnect your account with proper permissions.',
            extra_tags='permission_error'
        )
    except GmailAPIError as e:
        logger.error(f"Gmail API error for user {request.user.username}: {e}")
        messages.error(
            request,
            f'📧 Gmail service error: {str(e)}. Please try again later.',
            extra_tags='api_error'
        )
    except Exception as e:
        logger.error(f"Unexpected error during sync for user {request.user.username}: {e}")
        messages.error(
            request, 
            f'❌ Unexpected error occurred: {str(e)}. Please contact support if this persists.',
            extra_tags='unexpected_error'
        )
    
    return redirect('dashboard')


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
    
    return render(request, 'gmail_app/ai_config.html', context)


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
        ).order_by('-generated_at')
        
        # Get recent responses
        recent_responses = AIResponse.objects.filter(
            email_intent__email__gmail_account__user=request.user
        ).order_by('-generated_at')[:20]
        
        # Get email intents for analysis
        email_intents = EmailIntent.objects.filter(
            email__gmail_account__user=request.user
        ).order_by('-processed_at')[:50]
        
        context = {
            'ai_context': ai_context,
            'pending_responses': pending_responses,
            'recent_responses': recent_responses, 
            'email_intents': email_intents,
            'has_pending': pending_responses.exists(),
            'has_ai_config': True
        }
        
    except AIContext.DoesNotExist:
        context = {
            'has_ai_config': False,
            'ai_context': None,
            'pending_responses': [],
            'recent_responses': [],
            'email_intents': [],
            'has_pending': False
        }
    
    return render(request, 'gmail_app/ai_responses.html', context)


@login_required
def approve_response(request, response_id):
    """Approve AI response"""
    try:
        ai_response = AIResponse.objects.get(
            id=response_id,
            email_intent__email__gmail_account__user=request.user,
            status='pending_approval'
        )
        
        ai_response.status = 'approved' 
        ai_response.approved_at = timezone.now()
        ai_response.save()
        
        # Send the email immediately
        try:
            gmail_service = GmailService(request.user)
            sent_message_id = gmail_service.send_email(
                to_email=ai_response.email_intent.email.sender,
                subject=ai_response.response_subject,
                body=ai_response.response_text,
                reply_to_message_id=ai_response.email_intent.email.gmail_id
            )
            
            # Update status to sent
            ai_response.status = 'sent'
            ai_response.sent_at = timezone.now()
            ai_response.save()
            
            messages.success(request, f'📧 Response sent successfully to {ai_response.email_intent.email.sender}!')
            logger.info(f"Email sent by user {request.user.username} to {ai_response.email_intent.email.sender}")
            
        except Exception as e:
            logger.error(f"Error sending approved response {response_id}: {e}")
            messages.error(request, f'❌ Error sending email: {str(e)}. Response is approved but not sent.')
            
            # Keep as approved but not sent
            ai_response.status = 'approved'
            ai_response.save()
        
    except AIResponse.DoesNotExist:
        messages.error(request, '❌ Response not found or already processed')
    except Exception as e:
        logger.error(f"Error approving response for user {request.user.username}: {e}")
        messages.error(request, f'❌ Error approving response: {str(e)}')
    
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
        
        # Check emails
        total_emails = Email.objects.filter(gmail_account__user=request.user).count()
        processed_emails = EmailIntent.objects.filter(email__gmail_account__user=request.user).count()
        
        # Check responses
        total_responses = AIResponse.objects.filter(
            email_intent__email__gmail_account__user=request.user
        ).count()
        
        # Check temporal rules
        temporal_rules = TemporalRule.objects.filter(ai_context__user=request.user).count()
        
        debug_info = {
            'ai_context': ai_context_info,
            'emails': {
                'total': total_emails,
                'processed_by_ai': processed_emails,
                'unprocessed': total_emails - processed_emails
            },
            'responses': total_responses,
            'temporal_rules': temporal_rules,
            'openai_configured': bool(settings.OPENAI_API_KEY),
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