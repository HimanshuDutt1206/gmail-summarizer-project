import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Credentials
CREDENTIALS_DIR = os.path.join(BASE_DIR, 'credentials')
CREDENTIALS_FILE = os.path.join(CREDENTIALS_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(CREDENTIALS_DIR, 'token.json')

# Gmail API settings
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.modify']

# Database settings
DATABASE_URL = 'sqlite:///gmail_processor.db'

# Email processing settings
MAX_EMAILS_TO_PROCESS = 10
CHECK_INTERVAL_MINUTES = 15

# Categories for email classification
CATEGORIES = {
    'IMPORTANT': ['urgent', 'important', 'critical', 'asap'],
    'DEADLINE': ['deadline', 'due', 'by', 'before'],
    'ACTION_REQUIRED': ['action required', 'please respond', 'needs your attention'],
    'MEETING': ['meeting', 'schedule', 'appointment', 'call']
}
