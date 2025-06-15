import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
from config.config import SCOPES, CREDENTIALS_FILE, TOKEN_FILE


class GmailClient:
    def __init__(self):
        self.service = None
        self.creds = None

    def authenticate(self):
        """Handles the OAuth2 authentication flow."""
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                self.creds = flow.run_local_server(port=0)

            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('gmail', 'v1', credentials=self.creds)
        return self.service

    def list_messages(self, query='', max_results=10):
        """List messages in the user's mailbox."""
        try:
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results).execute()
            messages = results.get('messages', [])
            return messages
        except Exception as e:
            print(f'An error occurred: {e}')
            return []

    def get_message(self, msg_id):
        """Get a specific message by ID."""
        try:
            message = self.service.users().messages().get(
                userId='me', id=msg_id, format='full').execute()
            return message
        except Exception as e:
            print(f'An error occurred: {e}')
            return None

    def get_message_content(self, message):
        """Extract the content from a message."""
        if 'payload' not in message:
            return None

        payload = message['payload']
        headers = payload.get('headers', [])
        subject = next((header['value'] for header in headers
                       if header['name'].lower() == 'subject'), 'No Subject')

        if 'parts' in payload:
            parts = payload['parts']
            data = parts[0]['body'].get('data', '')
        else:
            data = payload['body'].get('data', '')

        if data:
            text = base64.urlsafe_b64decode(data).decode()
            return {
                'subject': subject,
                'content': text,
                'snippet': message.get('snippet', ''),
                'id': message['id']
            }
        return None

    def mark_as_read(self, msg_id):
        """Mark a message as read by removing the UNREAD label."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            print(f'An error occurred: {e}')
            return False
