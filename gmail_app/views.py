import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse
from .gmail_service import GmailService
from .models import Email, GmailAccount
from .exceptions import (
    RefreshTokenInvalidError, OAuthError, GmailAPIError, 
    QuotaExceededError, PermissionError
)

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
        messages.success(request, f'✅ Synced {len(synced_emails)} new emails successfully!')
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