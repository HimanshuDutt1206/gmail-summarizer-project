import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
import html
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

    def _extract_text_from_part(self, part):
        """Extract text content from a message part."""
        try:
            mime_type = part.get('mimeType', '')
            body = part.get('body', {})
            data = body.get('data', '')

            if not data:
                return ''

            # Decode base64 content
            try:
                decoded_data = base64.urlsafe_b64decode(data)
                text = decoded_data.decode('utf-8')
            except UnicodeDecodeError:
                # Try different encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        text = decoded_data.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # If all encodings fail, use error handling
                    text = decoded_data.decode('utf-8', errors='replace')

            # Clean HTML content if it's HTML
            if 'html' in mime_type.lower():
                # Simple HTML tag removal
                import re
                text = re.sub(r'<[^>]+>', '', text)
                text = html.unescape(text)

            return text.strip()

        except Exception as e:
            print(f"Error extracting text from part: {e}")
            return ''

    def _extract_content_recursive(self, payload):
        """Recursively extract content from email payload."""
        content_parts = []

        # Check if this part has direct content
        if 'body' in payload and payload['body'].get('data'):
            text = self._extract_text_from_part(payload)
            if text:
                content_parts.append(text)

        # Check for multipart content
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')

                # Skip attachments and images
                if mime_type.startswith('image/') or 'attachment' in str(part.get('filename', '')):
                    continue

                # Recursively process parts
                if 'parts' in part:
                    sub_content = self._extract_content_recursive(part)
                    content_parts.extend(sub_content)
                else:
                    # Extract text from this part
                    text = self._extract_text_from_part(part)
                    if text:
                        content_parts.append(text)

        return content_parts

    def get_message_content(self, message):
        """Extract the content from a message with improved handling."""
        try:
            if 'payload' not in message:
                return None

            payload = message['payload']
            headers = payload.get('headers', [])

            # Extract subject and other important headers
            subject = 'No Subject'
            date_header = ''
            sender = ''

            for header in headers:
                header_name = header['name'].lower()
                if header_name == 'subject':
                    subject = header['value']
                elif header_name == 'date':
                    date_header = header['value']
                elif header_name == 'from':
                    sender = header['value']

            # Extract content using recursive method
            content_parts = self._extract_content_recursive(payload)

            # Combine all content parts
            if content_parts:
                content = '\n\n'.join(content_parts)
            else:
                # Fallback to snippet if no content extracted
                content = message.get('snippet', '')

            # Clean up content
            content = content.strip()
            if not content:
                content = message.get('snippet', 'No content available')

            return {
                'subject': subject,
                'content': content,
                'snippet': message.get('snippet', ''),
                'id': message['id'],
                'date_header': date_header,
                'sender': sender,
                'received_time': message.get('internalDate', '')
            }

        except Exception as e:
            print(f"Error extracting message content: {e}")
            # Fallback: return basic info with snippet
            try:
                headers = message.get('payload', {}).get('headers', [])
                subject = next(
                    (h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')

                return {
                    'subject': subject,
                    'content': message.get('snippet', 'Content extraction failed'),
                    'snippet': message.get('snippet', ''),
                    'id': message['id']
                }
            except:
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
