"""
Management command to migrate GmailAccount data to EmailAccount
Run this after migrations: python manage.py migrate_to_emailaccount
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from gmail_app.models import GmailAccount, EmailAccount, Email


class Command(BaseCommand):
    help = 'Migrate existing GmailAccount data to EmailAccount model'

    def handle(self, *args, **options):
        self.stdout.write('Starting migration from GmailAccount to EmailAccount...')

        migrated = 0
        emails_updated = 0

        with transaction.atomic():
            for gmail_account in GmailAccount.objects.all():
                # Create or get EmailAccount from GmailAccount
                email_account, created = EmailAccount.objects.get_or_create(
                    user=gmail_account.user,
                    email=gmail_account.email,
                    provider='gmail',
                    defaults={
                        'access_token': gmail_account.access_token,
                        'refresh_token': gmail_account.refresh_token,
                        'token_expires_at': gmail_account.token_expires_at,
                        'is_active': True,
                    }
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created EmailAccount for {gmail_account.email}')
                    )
                    migrated += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'○ EmailAccount already exists for {gmail_account.email}')
                    )

                # Update all emails to point to new EmailAccount
                emails = Email.objects.filter(gmail_account=gmail_account, email_account__isnull=True)
                count = emails.count()

                if count > 0:
                    # Update email_account
                    for email in emails:
                        email.email_account = email_account
                        email.save(update_fields=['email_account'])

                    emails_updated += count
                    self.stdout.write(
                        self.style.SUCCESS(f'  → Updated {count} emails')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Migration complete!\n'
                f'   - EmailAccounts created: {migrated}\n'
                f'   - Emails updated: {emails_updated}'
            )
        )

        # Summary
        total_email_accounts = EmailAccount.objects.count()
        total_emails_with_account = Email.objects.filter(email_account__isnull=False).count()
        total_emails_legacy = Email.objects.filter(email_account__isnull=True, gmail_account__isnull=False).count()

        self.stdout.write(
            f'\n📊 Current state:\n'
            f'   - Total EmailAccounts: {total_email_accounts}\n'
            f'   - Emails using EmailAccount: {total_emails_with_account}\n'
            f'   - Emails still on legacy GmailAccount: {total_emails_legacy}'
        )

        if total_emails_legacy > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  Warning: {total_emails_legacy} emails still using legacy GmailAccount.\n'
                    f'   Run this command again to complete migration.'
                )
            )
