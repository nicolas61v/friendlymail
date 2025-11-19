"""
Outlook-specific views - OAuth connection, callback, synchronization
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..outlook_service import OutlookService
from ..models import EmailAccount

logger = logging.getLogger('gmail_app')


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
