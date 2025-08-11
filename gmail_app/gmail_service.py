import os
import json
import base64
from datetime import datetime, timezone
from django.conf import settings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from .models import GmailAccount, Email

# Allow insecure transport for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class GmailService:
    def __init__(self, user):
        self.user = user
        self.credentials = None
        self.service = None
    
    def get_authorization_url(self, request):
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
            include_granted_scopes='true'
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
        
        # Get user info
        service = build('gmail', 'v1', credentials=credentials)
        profile = service.users().getProfile(userId='me').execute()
        
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
                credentials.refresh(Request())
                gmail_account.access_token = credentials.token
                gmail_account.token_expires_at = datetime.fromtimestamp(credentials.expiry.timestamp(), tz=timezone.utc)
                gmail_account.save()
            
            return credentials
        except GmailAccount.DoesNotExist:
            return None
    
    def get_service(self):
        if not self.credentials:
            self.credentials = self.get_credentials()
        
        if self.credentials:
            self.service = build('gmail', 'v1', credentials=self.credentials)
            return self.service
        return None
    
    def sync_emails(self, max_results=20):
        service = self.get_service()
        if not service:
            return []
        
        gmail_account = GmailAccount.objects.get(user=self.user)
        
        # Get messages
        results = service.users().messages().list(
            userId='me', 
            maxResults=max_results,
            q='in:inbox'
        ).execute()
        
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