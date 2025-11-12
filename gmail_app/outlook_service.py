"""
Outlook/Microsoft Graph API Service
Handles OAuth2 authentication and email operations for Office 365/Outlook
"""
import msal
import requests
import secrets
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from gmail_app.models import EmailAccount, Email


logger = logging.getLogger('gmail_app')


class OutlookService:
    """
    Service for interacting with Microsoft Graph API (Outlook/Office 365)
    Similar architecture to GmailService but for Microsoft ecosystem
    """

    def __init__(self, user):
        self.user = user
        self.client_id = settings.OUTLOOK_CLIENT_ID
        self.client_secret = settings.OUTLOOK_CLIENT_SECRET
        self.authority = settings.OUTLOOK_AUTHORITY
        self.redirect_uri = settings.OUTLOOK_REDIRECT_URI
        self.scopes = settings.OUTLOOK_SCOPES

    def get_authorization_url(self, request):
        """
        Generate Microsoft OAuth2 authorization URL

        Args:
            request: Django request object (for session state storage)

        Returns:
            str: Authorization URL to redirect user to
        """
        # Create MSAL confidential client
        msal_app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        request.session['outlook_oauth_state'] = state

        # Generate authorization URL
        auth_url = msal_app.get_authorization_request_url(
            scopes=self.scopes,
            state=state,
            redirect_uri=self.redirect_uri
        )

        logger.info(f"Generated Outlook authorization URL for user {self.user.username}")
        return auth_url

    def handle_oauth_callback(self, request):
        """
        Process OAuth2 callback and store tokens

        Args:
            request: Django request object with OAuth callback parameters

        Returns:
            EmailAccount: Created or updated email account

        Raises:
            Exception: If OAuth flow fails
        """
        # Validate CSRF state
        state = request.GET.get('state')
        stored_state = request.session.get('outlook_oauth_state')

        if not state or state != stored_state:
            raise Exception("Invalid state parameter - possible CSRF attack")

        # Get authorization code
        code = request.GET.get('code')
        if not code:
            error = request.GET.get('error')
            error_description = request.GET.get('error_description', 'Unknown error')
            raise Exception(f"OAuth error: {error} - {error_description}")

        # Create MSAL app
        msal_app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )

        # Exchange code for tokens
        result = msal_app.acquire_token_by_authorization_code(
            code=code,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )

        if 'error' in result:
            raise Exception(f"Token acquisition failed: {result.get('error_description')}")

        # Extract tokens
        access_token = result['access_token']
        refresh_token = result.get('refresh_token')
        expires_in = result.get('expires_in', 3600)  # Default 1 hour

        if not refresh_token:
            raise Exception(
                "No refresh token received. Ensure 'offline_access' scope is included in OUTLOOK_SCOPES"
            )

        # Get user email from Microsoft Graph
        user_email = self._get_user_email(access_token)

        # Calculate token expiration
        token_expires_at = timezone.now() + timedelta(seconds=expires_in)

        # Create or update EmailAccount
        email_account, created = EmailAccount.objects.update_or_create(
            user=self.user,
            email=user_email,
            provider='outlook',
            defaults={
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_expires_at': token_expires_at,
                'is_active': True
            }
        )

        action = 'created' if created else 'updated'
        logger.info(f"Outlook account {action}: {user_email} for user {self.user.username}")

        # Clean up session
        if 'outlook_oauth_state' in request.session:
            del request.session['outlook_oauth_state']

        return email_account

    def _get_user_email(self, access_token):
        """
        Get user email from Microsoft Graph API

        Args:
            access_token: Valid Microsoft access token

        Returns:
            str: User's email address
        """
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)

        if response.status_code != 200:
            raise Exception(f"Failed to get user info: {response.text}")

        user_data = response.json()
        # Use 'mail' if available, otherwise fall back to 'userPrincipalName'
        return user_data.get('mail') or user_data.get('userPrincipalName')

    def get_credentials(self):
        """
        Get valid access token, refreshing if necessary

        Returns:
            str: Valid access token

        Raises:
            Exception: If no active Outlook account found or refresh fails
        """
        try:
            account = EmailAccount.objects.get(
                user=self.user,
                provider='outlook',
                is_active=True
            )
        except EmailAccount.DoesNotExist:
            raise Exception("No active Outlook account found. Please connect your Outlook account.")

        # Check if token expired
        if timezone.now() >= account.token_expires_at:
            logger.info(f"Access token expired for {account.email}, refreshing...")
            account = self._refresh_token(account)

        return account.access_token

    def _refresh_token(self, account):
        """
        Refresh access token using refresh token

        Args:
            account: EmailAccount instance

        Returns:
            EmailAccount: Updated account with new tokens
        """
        msal_app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )

        result = msal_app.acquire_token_by_refresh_token(
            refresh_token=account.refresh_token,
            scopes=self.scopes
        )

        if 'error' in result:
            logger.error(f"Token refresh failed: {result.get('error_description')}")
            account.is_active = False
            account.save()
            raise Exception(
                f"Failed to refresh token: {result.get('error_description')}. "
                "Please reconnect your Outlook account."
            )

        # Update tokens
        account.access_token = result['access_token']
        if 'refresh_token' in result:
            account.refresh_token = result['refresh_token']

        expires_in = result.get('expires_in', 3600)
        account.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
        account.save()

        logger.info(f"Successfully refreshed token for {account.email}")
        return account

    def sync_emails(self, max_results=50):
        """
        Sync emails from Microsoft Graph API

        Args:
            max_results: Maximum number of emails to fetch (default 50)

        Returns:
            dict: Sync results with counts
        """
        access_token = self.get_credentials()
        account = EmailAccount.objects.get(
            user=self.user,
            provider='outlook',
            is_active=True
        )

        # Microsoft Graph API endpoint
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {
            '$top': max_results,
            '$orderby': 'receivedDateTime desc',
            '$select': 'id,subject,from,toRecipients,receivedDateTime,body,isRead,importance'
        }

        response = requests.get(
            'https://graph.microsoft.com/v1.0/me/messages',
            headers=headers,
            params=params
        )

        if response.status_code != 200:
            raise Exception(f"Failed to fetch emails: {response.text}")

        messages = response.json().get('value', [])

        new_count = 0
        updated_count = 0

        for msg in messages:
            msg_id = msg['id']

            # Extract email data
            subject = msg.get('subject', '')[:500]  # Limit to 500 chars

            from_data = msg.get('from', {}).get('emailAddress', {})
            sender = from_data.get('address', '')[:255]

            # Get first recipient (can have multiple)
            recipients = msg.get('toRecipients', [])
            recipient = ''
            if recipients:
                recipient = recipients[0].get('emailAddress', {}).get('address', '')[:255]

            # Parse received date
            received_date_str = msg.get('receivedDateTime')
            if received_date_str:
                # Remove 'Z' and parse as UTC
                received_date = datetime.fromisoformat(received_date_str.replace('Z', '+00:00'))
            else:
                received_date = timezone.now()

            # Extract body
            body_content = msg.get('body', {})
            content_type = body_content.get('contentType', 'text')
            content = body_content.get('content', '')

            if content_type == 'html':
                body_html = content
                body_plain = ''  # Could add HTML to text conversion here
            else:
                body_plain = content
                body_html = ''

            # Flags
            is_read = msg.get('isRead', False)
            is_important = msg.get('importance') == 'high'

            # Thread ID (Outlook uses conversationId)
            thread_id = msg.get('conversationId', msg_id)

            # Create or update email
            email, created = Email.objects.update_or_create(
                email_account=account,
                provider_id=msg_id,
                defaults={
                    'thread_id': thread_id,
                    'subject': subject,
                    'sender': sender,
                    'recipient': recipient,
                    'body_plain': body_plain,
                    'body_html': body_html,
                    'received_date': received_date,
                    'is_read': is_read,
                    'is_important': is_important
                }
            )

            if created:
                new_count += 1
            else:
                updated_count += 1

        logger.info(
            f"Outlook sync complete for {account.email}: "
            f"{new_count} new, {updated_count} updated"
        )

        return {
            'new_emails': new_count,
            'updated_emails': updated_count,
            'total_synced': len(messages)
        }

    def send_email(self, to, subject, body, is_html=True):
        """
        Send email using Microsoft Graph API

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether body is HTML (default True)

        Returns:
            bool: True if sent successfully
        """
        access_token = self.get_credentials()

        # Build message payload
        message = {
            'subject': subject,
            'body': {
                'contentType': 'HTML' if is_html else 'Text',
                'content': body
            },
            'toRecipients': [
                {
                    'emailAddress': {
                        'address': to
                    }
                }
            ]
        }

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Send email
        response = requests.post(
            'https://graph.microsoft.com/v1.0/me/sendMail',
            headers=headers,
            json={'message': message}
        )

        if response.status_code not in [200, 202]:
            raise Exception(f"Failed to send email: {response.text}")

        logger.info(f"Email sent successfully to {to} via Outlook")
        return True

    def disconnect(self):
        """
        Deactivate Outlook account

        Returns:
            bool: True if deactivated successfully
        """
        try:
            account = EmailAccount.objects.get(
                user=self.user,
                provider='outlook',
                is_active=True
            )
            account.is_active = False
            account.save()
            logger.info(f"Deactivated Outlook account: {account.email}")
            return True
        except EmailAccount.DoesNotExist:
            return False
