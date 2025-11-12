from django.db import models
from django.contrib.auth.models import User


class EmailAccount(models.Model):
    """
    Unified email account model supporting multiple providers (Gmail, Outlook, etc.)
    Allows users to connect multiple accounts from different providers
    """
    PROVIDER_CHOICES = [
        ('gmail', 'Gmail'),
        ('outlook', 'Outlook/Office 365'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_accounts')
    email = models.EmailField()
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)

    # OAuth2 tokens
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    token_expires_at = models.DateTimeField()

    # Account status
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Prevent duplicate accounts (same user + email + provider)
        unique_together = [['user', 'email', 'provider']]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.provider}) - {self.user.username}"


class GmailAccount(models.Model):
    """
    DEPRECATED: Legacy model for backward compatibility
    Will be migrated to EmailAccount
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    token_expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.email} - {self.user.username}"


class Email(models.Model):
    """
    Email model supporting multiple providers
    """
    # New unified account (supports multiple providers)
    email_account = models.ForeignKey(
        EmailAccount,
        on_delete=models.CASCADE,
        related_name='emails',
        null=True,  # Temporary for migration
        blank=True
    )

    # Legacy Gmail account (for backward compatibility during migration)
    gmail_account = models.ForeignKey(
        GmailAccount,
        on_delete=models.CASCADE,
        related_name='emails',
        null=True,
        blank=True
    )

    # Provider-specific ID (gmail_id, outlook_id, etc.)
    provider_id = models.CharField(max_length=255, db_index=True, default='temp')
    thread_id = models.CharField(max_length=255, default='')

    # Email content
    subject = models.CharField(max_length=500, blank=True)
    sender = models.CharField(max_length=255)
    recipient = models.CharField(max_length=255)
    body_plain = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    received_date = models.DateTimeField(db_index=True)  # Index for sorting

    # Flags
    is_read = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-received_date']  # Most recent first
        # Prevent duplicate emails per account
        indexes = [
            models.Index(fields=['-received_date']),  # Fast sorting
            models.Index(fields=['email_account', 'provider_id']),  # Fast lookups
        ]

    def __str__(self):
        return f"{self.subject[:50]} - {self.sender}"

    @property
    def provider(self):
        """Get provider from email_account"""
        if self.email_account:
            return self.email_account.provider
        return 'gmail'  # Legacy default