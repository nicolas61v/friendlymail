"""
Query helpers to eliminate duplicate query patterns across views

This module provides reusable query helpers that centralize common
database query patterns, reducing code duplication and improving maintainability.
"""
from django.db.models import Q
from .models import Email, EmailAccount, GmailAccount
from .ai_models import AIResponse, EmailIntent


def get_user_email_accounts(user, active_only=True):
    """
    Get all email accounts for a user

    Args:
        user: Django User instance
        active_only: If True, only return active accounts (default: True)

    Returns:
        QuerySet of EmailAccount objects
    """
    queryset = EmailAccount.objects.filter(user=user)
    if active_only:
        queryset = queryset.filter(is_active=True)
    return queryset


def get_user_emails(user, email_accounts=None, gmail_accounts=None):
    """
    Get all emails for a user (from both EmailAccount and legacy GmailAccount)

    Args:
        user: Django User instance
        email_accounts: Optional EmailAccount queryset (will be fetched if not provided)
        gmail_accounts: Optional GmailAccount queryset (will be fetched if not provided)

    Returns:
        QuerySet of Email objects
    """
    if email_accounts is None:
        email_accounts = EmailAccount.objects.filter(user=user)

    if gmail_accounts is None:
        gmail_accounts = GmailAccount.objects.filter(user=user)

    return Email.objects.filter(
        Q(email_account__in=email_accounts) | Q(gmail_account__in=gmail_accounts)
    )


def get_user_ai_response(user, response_id, status_filter=None):
    """
    Get an AI response owned by the user (supports both email_account and gmail_account)

    Args:
        user: Django User instance
        response_id: ID of the AIResponse
        status_filter: Optional status or list of statuses to filter by

    Returns:
        AIResponse instance

    Raises:
        AIResponse.DoesNotExist: If response not found or user doesn't have access
    """
    query = Q(email_intent__email__gmail_account__user=user) | \
            Q(email_intent__email__email_account__user=user)

    if status_filter:
        if isinstance(status_filter, str):
            return AIResponse.objects.get(query, id=response_id, status=status_filter)
        else:
            # Assume it's a list/tuple of statuses
            return AIResponse.objects.get(query, id=response_id, status__in=status_filter)
    else:
        return AIResponse.objects.get(query, id=response_id)


def get_user_ai_responses_by_status(user, status):
    """
    Get all AI responses for a user filtered by status

    Args:
        user: Django User instance
        status: Status to filter by (e.g., 'pending_approval', 'sent', 'approved')

    Returns:
        QuerySet of AIResponse objects
    """
    return AIResponse.objects.filter(
        Q(email_intent__email__email_account__user=user) |
        Q(email_intent__email__gmail_account__user=user),
        status=status
    ).select_related('email_intent__email')


def get_unprocessed_emails(user, limit=10):
    """
    Get emails that haven't been processed by AI yet

    Args:
        user: Django User instance
        limit: Maximum number of emails to return (default: 10)

    Returns:
        QuerySet of unprocessed Email objects
    """
    return Email.objects.filter(
        Q(email_account__user=user) | Q(gmail_account__user=user)
    ).exclude(
        id__in=EmailIntent.objects.values('email_id')
    )[:limit]


def count_user_emails(user):
    """
    Count total emails for a user

    Args:
        user: Django User instance

    Returns:
        int: Total number of emails
    """
    email_accounts = EmailAccount.objects.filter(user=user)
    gmail_accounts = GmailAccount.objects.filter(user=user)

    return Email.objects.filter(
        Q(email_account__in=email_accounts) | Q(gmail_account__in=gmail_accounts)
    ).count()


def count_user_responded_emails(user):
    """
    Count emails that have AI responses

    Args:
        user: Django User instance

    Returns:
        int: Number of emails with AI responses
    """
    email_accounts = EmailAccount.objects.filter(user=user)
    gmail_accounts = GmailAccount.objects.filter(user=user)

    return EmailIntent.objects.filter(
        Q(email__email_account__in=email_accounts) |
        Q(email__gmail_account__in=gmail_accounts),
        airesponse__isnull=False
    ).distinct().count()


def verify_email_ownership(email, user):
    """
    Verify that a user owns an email (through either email_account or gmail_account)

    Args:
        email: Email instance
        user: Django User instance

    Returns:
        bool: True if user owns the email, False otherwise
    """
    return (email.email_account and email.email_account.user == user) or \
           (email.gmail_account and email.gmail_account.user == user)
