"""
Email management views - Dashboard, email details, synchronization
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Case, When, Value, IntegerField
from ..models import Email, EmailAccount, GmailAccount
from ..ai_models import AIRole, EmailIntent, AIResponse
from ..ai_service import EmailAIProcessor
from ..gmail_service import GmailService
from ..outlook_service import OutlookService
from ..exceptions import (
    RefreshTokenInvalidError, GmailAPIError,
    QuotaExceededError, PermissionError
)

logger = logging.getLogger('gmail_app')


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
def email_detail(request, email_id):
    try:
        # Support both new (email_account) and legacy (gmail_account) models
        email = Email.objects.get(
            id=email_id,
            email_account__user=request.user
        )
    except Email.DoesNotExist:
        # Fallback to legacy model for backward compatibility
        try:
            email = Email.objects.get(
                id=email_id,
                gmail_account__user=request.user
            )
        except Email.DoesNotExist:
            messages.error(request, 'Email not found')
            return redirect('dashboard')

    return render(request, 'gmail_app/email_detail.html', {'email': email})


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
            # Get active AIRole
            ai_context = AIRole.get_active_role(request.user)

            if ai_context and synced_emails:
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
                    'synced': len(synced_emails),
                    'message': f'✅ Synced {len(synced_emails)} new emails successfully!',
                    'ai_enabled': False
                })

        except Exception as e:
            logger.error(f"Error getting AI context for user {request.user.username}: {e}")
            return JsonResponse({
                'success': True,
                'synced': len(synced_emails),
                'message': f'✅ Synced {len(synced_emails)} new emails successfully!',
                'ai_enabled': False
            })

    except RefreshTokenInvalidError as e:
        logger.warning(f"Token expired for user {request.user.username}: {e}")
        # Delete the expired account to force reconnection
        GmailAccount.objects.filter(user=request.user).delete()
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

        # Sync Gmail accounts (now supports multiple accounts!)
        gmail_accounts = email_accounts.filter(provider='gmail')
        for account in gmail_accounts:
            try:
                gmail_service = GmailService(request.user)
                # Now syncs specific Gmail account by ID (supports multiple)
                synced_emails = gmail_service.sync_emails(email_account_id=account.id)
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


@login_required
def get_all_emails_with_ai_status(request):
    """API endpoint para obtener todos los emails con su estado de IA"""
    try:
        # Obtener todos los emails del usuario
        email_accounts = EmailAccount.objects.filter(user=request.user)
        gmail_accounts = GmailAccount.objects.filter(user=request.user)

        emails = Email.objects.filter(
            Q(email_account__in=email_accounts) | Q(gmail_account__in=gmail_accounts)
        ).order_by('-received_date')

        # Preparar datos para la tabla
        email_data = []
        for email in emails:
            has_intent = hasattr(email, 'emailintent')

            if has_intent:
                intent = email.emailintent
                ai_decision_value = 1 if intent.ai_decision == 'respond' else 0
                has_response = hasattr(intent, 'airesponse')
                response_id = intent.airesponse.id if has_response else None
                response_status = intent.airesponse.status if has_response else None
            else:
                ai_decision_value = None
                has_response = False
                response_id = None
                response_status = None

            email_data.append({
                'id': email.id,
                'subject': email.subject,
                'sender': email.sender,
                'received_date': email.received_date,
                'has_intent': has_intent,
                'ai_decision': ai_decision_value,  # 1 para respond, 0 para escalate
                'has_response': has_response,
                'response_id': response_id,  # ID of the AIResponse if exists
                'response_status': response_status,
                'intent_type': intent.intent_type if has_intent else None,
                'confidence': intent.confidence_score if has_intent else None,
            })

        return JsonResponse({
            'success': True,
            'emails': email_data
        })

    except Exception as e:
        logger.error(f"Error getting email status for user {request.user.username}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
