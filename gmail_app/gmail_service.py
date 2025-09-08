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
from .models import GmailAccount, Email
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
        
        # Save or update Gmail account
        gmail_account, created = GmailAccount.objects.update_or_create(
            user=self.user,
            defaults={
                'email': profile['emailAddress'],
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_expires_at': datetime.fromtimestamp(credentials.expiry.timestamp(), tz=timezone.utc)
            }
        )
        
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
    
    def sync_emails(self, max_results=20):
        logger.info(f"Starting email sync for user {self.user.username}")
        
        try:
            service = self.get_service()
            if not service:
                raise OAuthError("Unable to connect to Gmail service. Please reconnect your account.")
            
            gmail_account = GmailAccount.objects.get(user=self.user)
            
            # Get messages
            results = service.users().messages().list(
                userId='me', 
                maxResults=max_results,
                q='in:inbox'
            ).execute()
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
            
            # Save email to database
            email, created = Email.objects.update_or_create(
                gmail_id=msg['id'],
                defaults={
                    'gmail_account': gmail_account,
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
        
        return synced_emails