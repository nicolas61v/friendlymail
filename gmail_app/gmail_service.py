import os
import json
import base64
import logging
from datetime import datetime, timezone
from django.conf import settings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
from .models import GmailAccount, EmailAccount, Email
from .exceptions import (
    OAuthError, TokenExpiredError, RefreshTokenInvalidError,
    GmailAPIError, QuotaExceededError, PermissionError
)

logger = logging.getLogger('gmail_app')

# Allow insecure transport for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class GmailService:
    def __init__(self, user):
        self.user = user
        self.credentials = None
        self.service = None
    
    def get_authorization_url(self, request):
        # Clear any existing OAuth state to prevent scope conflicts
        if 'oauth_state' in request.session:
            del request.session['oauth_state']
            logger.info(f"Cleared existing OAuth state for user {self.user.username}")
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                    "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [request.build_absolute_uri('/gmail/callback/')]
                }
            },
            scopes=settings.GMAIL_SCOPES
        )
        flow.redirect_uri = request.build_absolute_uri('/gmail/callback/')
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force refresh_token to be returned
        )
        request.session['oauth_state'] = state
        return authorization_url
    
    def handle_oauth_callback(self, request):
        state = request.session.get('oauth_state')
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                    "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [request.build_absolute_uri('/gmail/callback/')]
                }
            },
            scopes=settings.GMAIL_SCOPES,
            state=state
        )
        flow.redirect_uri = request.build_absolute_uri('/gmail/callback/')
        
        authorization_response = request.build_absolute_uri()
        flow.fetch_token(authorization_response=authorization_response)
        
        credentials = flow.credentials
        
        # Validate refresh_token
        if not credentials.refresh_token:
            logger.error(f"No refresh_token received for user {self.user.username}")
            raise OAuthError(
                "Authorization incomplete. Please disconnect any existing Gmail connections in your Google account and try again.",
                error_type="no_refresh_token",
                error_description="Google did not provide a refresh token. This usually happens when the app was previously authorized."
            )
        
        # Get user info
        service = build('gmail', 'v1', credentials=credentials)
        profile = service.users().getProfile(userId='me').execute()
        
        logger.info(f"Successfully authenticated Gmail for user {self.user.username}, email: {profile['emailAddress']}")
        
        # Save or update Gmail account (legacy model for backward compatibility)
        gmail_account, created = GmailAccount.objects.update_or_create(
            user=self.user,
            defaults={
                'email': profile['emailAddress'],
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_expires_at': datetime.fromtimestamp(credentials.expiry.timestamp(), tz=timezone.utc)
            }
        )

        # ALSO create/update unified EmailAccount model (required for new multi-account system)
        email_account, ea_created = EmailAccount.objects.update_or_create(
            user=self.user,
            email=profile['emailAddress'],
            provider='gmail',
            defaults={
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_expires_at': datetime.fromtimestamp(credentials.expiry.timestamp(), tz=timezone.utc),
                'is_active': True
            }
        )

        action = "connected" if ea_created else "updated"
        logger.info(f"EmailAccount {action} for user {self.user.username}: {email_account.email} ({email_account.provider})")

        return gmail_account
    
    def get_credentials(self):
        try:
            gmail_account = GmailAccount.objects.get(user=self.user)
            credentials = Credentials(
                token=gmail_account.access_token,
                refresh_token=gmail_account.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
                client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                scopes=settings.GMAIL_SCOPES
            )
            
            if credentials.expired:
                logger.info(f"Refreshing expired token for user {self.user.username}")
                try:
                    credentials.refresh(Request())
                    gmail_account.access_token = credentials.token
                    gmail_account.token_expires_at = datetime.fromtimestamp(credentials.expiry.timestamp(), tz=timezone.utc)
                    gmail_account.save()
                    logger.info(f"Token refreshed successfully for user {self.user.username}")
                except RefreshError as e:
                    logger.error(f"Failed to refresh token for user {self.user.username}: {e}")
                    # Check if it's specifically an invalid_grant error
                    error_str = str(e)
                    if 'invalid_grant' in error_str:
                        raise RefreshTokenInvalidError(
                            "Your Gmail access has expired. Please reconnect your account.",
                            error_type="invalid_grant",
                            error_description=error_str
                        )
                    else:
                        raise OAuthError(f"Token refresh failed: {error_str}")
                except Exception as e:
                    error_str = str(e)
                    # Also catch invalid_grant errors that come as generic exceptions
                    if 'invalid_grant' in error_str or 'Bad Request' in error_str:
                        logger.error(f"Invalid grant error for user {self.user.username}: {e}")
                        raise RefreshTokenInvalidError(
                            "Your Gmail access has expired. Please reconnect your account.",
                            error_type="invalid_grant", 
                            error_description=error_str
                        )
                    else:
                        raise
            
            return credentials
        except GmailAccount.DoesNotExist:
            logger.warning(f"No Gmail account found for user {self.user.username}")
            return None
    
    def get_service(self):
        if not self.credentials:
            self.credentials = self.get_credentials()
        
        if self.credentials:
            self.service = build('gmail', 'v1', credentials=self.credentials)
            return self.service
        return None
    
    def sync_emails(self, max_results=20, email_account_id=None):
        """
        Sync emails from Gmail API

        Args:
            max_results (int): Maximum number of emails to fetch (default: 20)
            email_account_id (int): Specific EmailAccount ID to sync. If None, syncs the first active account.
                                   This enables multiple Gmail accounts to be synced.

        Returns:
            list: List of newly created Email objects
        """
        logger.info(f"Starting email sync for user {self.user.username}")

        try:
            service = self.get_service()
            if not service:
                raise OAuthError("Unable to connect to Gmail service. Please reconnect your account.")

            # Get the specific email account to sync
            if email_account_id:
                email_account = EmailAccount.objects.get(
                    id=email_account_id,
                    user=self.user,
                    provider='gmail',
                    is_active=True
                )
                logger.info(f"Syncing specific Gmail account: {email_account.email}")
            else:
                # Get first active Gmail account for backward compatibility
                email_account = EmailAccount.objects.filter(
                    user=self.user,
                    provider='gmail',
                    is_active=True
                ).first()

            if not email_account:
                raise OAuthError("No active Gmail account found. Please reconnect your account.")

            # Get messages
            results = service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q='in:inbox'
            ).execute()
        except EmailAccount.DoesNotExist:
            raise OAuthError(f"Gmail account with ID {email_account_id} not found.")
        except HttpError as e:
            logger.error(f"Gmail API error during sync for user {self.user.username}: {e}")
            if e.resp.status == 403:
                raise PermissionError(
                    "Insufficient permissions to access Gmail. Please reconnect your account.",
                    status_code=403,
                    error_details=str(e)
                )
            elif e.resp.status == 429:
                raise QuotaExceededError(
                    "Gmail API quota exceeded. Please try again later.",
                    status_code=429,
                    error_details=str(e)
                )
            else:
                raise GmailAPIError(
                    f"Gmail API error: {e}",
                    status_code=e.resp.status,
                    error_details=str(e)
                )

        messages = results.get('messages', [])
        synced_emails = []

        for message in messages:
            msg = service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'
            ).execute()

            # Extract email data
            headers = msg['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            to = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown')
            date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')

            # Parse date
            try:
                received_date = datetime.strptime(date_str.split(' (')[0], '%a, %d %b %Y %H:%M:%S %z')
            except:
                received_date = datetime.now(timezone.utc)

            # Extract body
            body_plain = ''
            body_html = ''

            def extract_body(payload):
                nonlocal body_plain, body_html
                if 'parts' in payload:
                    for part in payload['parts']:
                        extract_body(part)
                else:
                    if payload.get('mimeType') == 'text/plain':
                        data = payload['body'].get('data', '')
                        if data:
                            body_plain = base64.urlsafe_b64decode(data).decode('utf-8')
                    elif payload.get('mimeType') == 'text/html':
                        data = payload['body'].get('data', '')
                        if data:
                            body_html = base64.urlsafe_b64decode(data).decode('utf-8')

            extract_body(msg['payload'])

            # Save email to database (using new unified model)
            email, created = Email.objects.update_or_create(
                email_account=email_account,
                provider_id=msg['id'],
                defaults={
                    'thread_id': msg['threadId'],
                    'subject': subject,
                    'sender': sender,
                    'recipient': to,
                    'body_plain': body_plain,
                    'body_html': body_html,
                    'received_date': received_date,
                    'is_read': 'UNREAD' not in msg['labelIds']
                }
            )

            if created:
                synced_emails.append(email)
                logger.info(f"New email synced from {email_account.email}: {subject[:50]}")

        logger.info(f"Sync complete for {email_account.email}: {len(synced_emails)} new emails")
        return synced_emails
    
    def send_email(self, to_email: str, subject: str, body: str, reply_to_message_id: str = None):
        """Send email via Gmail API"""
        service = self.get_service()
        if not service:
            raise OAuthError("Unable to connect to Gmail service for sending")
        
        logger.info(f"Sending email to {to_email} with subject: {subject[:50]}")
        
        try:
            # Create message
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import base64
            from email.utils import parseaddr

            # Extract email address if it contains display name
            # Convert "Name <email@domain.com>" to "email@domain.com"
            _, clean_email = parseaddr(to_email)
            if not clean_email:
                clean_email = to_email

            message = MIMEMultipart()
            message['to'] = clean_email
            message['subject'] = subject
            
            # Add reply headers if replying to a message
            if reply_to_message_id:
                message['In-Reply-To'] = reply_to_message_id
                message['References'] = reply_to_message_id
            
            # Add body
            msg_body = MIMEText(body, 'plain', 'utf-8')
            message.attach(msg_body)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send message
            sent_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email sent successfully. Message ID: {sent_message['id']}")
            return sent_message['id']
            
        except Exception as e:
            error_msg = str(e) if str(e) else type(e).__name__
            logger.error(f"Error sending email to {to_email}: {error_msg}")
            logger.exception("Stack trace:")  # Log full stack trace for debugging
            raise GmailAPIError(f"Failed to send email: {error_msg}")