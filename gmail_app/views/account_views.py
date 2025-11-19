"""
Generic account management views
"""
import logging
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import EmailAccount

logger = logging.getLogger('gmail_app')


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
