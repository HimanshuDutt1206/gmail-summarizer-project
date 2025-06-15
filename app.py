from flask import Flask, render_template, jsonify, request
import webbrowser
import threading
import time
import json
import os
from datetime import datetime
from src.gmail_client import GmailClient
from src.llm_service import LLMService
from config.config import MAX_EMAILS_TO_PROCESS

app = Flask(__name__)

# Simple JSON file storage instead of database
DATA_FILE = 'emails_data.json'


def load_emails():
    """Load emails from JSON file."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def save_emails(emails):
    """Save emails to JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(emails, f, indent=2)


def simple_categorize_email(subject, content):
    """Simple categorization without spaCy."""
    text = f"{subject} {content}".lower()
    categories = []

    # Define categories
    CATEGORIES = {
        'IMPORTANT': ['urgent', 'important', 'critical', 'asap'],
        'DEADLINE': ['deadline', 'due', 'by', 'before'],
        'ACTION_REQUIRED': ['action required', 'please respond', 'needs your attention'],
        'MEETING': ['meeting', 'schedule', 'appointment', 'call']
    }

    for category, keywords in CATEGORIES.items():
        if any(keyword.lower() in text for keyword in keywords):
            categories.append(category)

    return categories


def simple_summarize_email(content):
    """Simple summarization without spaCy."""
    sentences = content.split('.')
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) > 1:
        summary = f"{sentences[0]}... {sentences[-1]}"
    elif len(sentences) == 1:
        summary = sentences[0]
    else:
        summary = "No content to summarize"

    # Limit summary length
    if len(summary) > 200:
        summary = summary[:200] + "..."

    return summary


def process_email_with_llm(email_data, llm_service):
    """Process a single email with LLM-powered analysis."""
    if not email_data:
        return None

    subject = email_data.get('subject', '')
    content = email_data.get('content', '')

    print(f"[DEBUG] Processing email with LLM: {subject[:50]}...")

    # Get comprehensive LLM analysis
    analysis = llm_service.analyze_email_comprehensive(subject, content)

    if analysis:
        # Use LLM analysis results
        importance_level = analysis.get('importance_level', 'UNIMPORTANT')
        summary = analysis.get('summary', 'No summary available')
        deadlines = analysis.get('deadlines', [])
        has_deadline = analysis.get('has_deadline', False)

        print(f"[DEBUG] LLM Analysis - Importance: {importance_level}")
        print(f"[DEBUG] Summary: {summary[:100]}...")
        print(f"[DEBUG] Deadlines: {deadlines}")
    else:
        # Fallback to individual methods
        categories = llm_service.categorize_email(subject, content)
        importance_level = categories[0] if categories else 'UNIMPORTANT'
        summary = llm_service.summarize_email(content)
        deadlines = llm_service.extract_deadlines(subject, content)
        has_deadline = len(deadlines) > 0

        print(f"[DEBUG] Fallback Analysis - Importance: {importance_level}")
        print(f"[DEBUG] Summary: {summary[:100]}...")
        print(f"[DEBUG] Deadlines: {deadlines}")

    return {
        'id': email_data.get('id'),
        'subject': subject,
        'importance_level': importance_level,
        'categories': [importance_level],  # For backward compatibility
        'deadlines': deadlines,
        'summary': summary,
        'is_important': importance_level in ['VERY_IMPORTANT', 'IMPORTANT'],
        'has_deadline': has_deadline or len(deadlines) > 0,
        'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }


def process_email_simple(email_data):
    """Process a single email with simple text processing (fallback)."""
    if not email_data:
        return None

    subject = email_data.get('subject', '')
    content = email_data.get('content', '')

    # Get categories
    categories = simple_categorize_email(subject, content)

    # Generate summary
    summary = simple_summarize_email(content)

    return {
        'id': email_data.get('id'),
        'subject': subject,
        'categories': categories,
        'deadlines': [],  # Simplified for now
        'summary': summary,
        'is_important': 'IMPORTANT' in categories,
        'has_deadline': 'DEADLINE' in categories,
        'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }


@app.route('/')
def index():
    """Main page with summarize button."""
    return render_template('index.html')


@app.route('/api/process-emails', methods=['POST'])
def process_emails():
    """Process current unread emails and return results."""
    try:
        # Clear previous emails
        save_emails([])

        gmail_client = GmailClient()

        # Initialize LLM service
        print("[DEBUG] Initializing LLM service...")
        llm_service = LLMService()

        # Check if API key is available
        use_llm = llm_service.api_key is not None
        if use_llm:
            print("[DEBUG] Using LLM-powered processing")
        else:
            print("[DEBUG] API key not found, using simple processing")

        print("[DEBUG] Authenticating with Gmail API...")
        gmail_client.authenticate()

        print("[DEBUG] Fetching unread messages...")
        messages = gmail_client.list_messages(
            query='is:unread in:inbox', max_results=MAX_EMAILS_TO_PROCESS)

        processed_emails = []

        for message in messages:
            print(f"[DEBUG] Processing message ID: {message['id']}")
            full_message = gmail_client.get_message(message['id'])
            if not full_message:
                continue

            email_data = gmail_client.get_message_content(full_message)
            if not email_data:
                continue

            # Use LLM processing if available, otherwise fallback to simple
            if use_llm:
                processed_data = process_email_with_llm(
                    email_data, llm_service)
            else:
                processed_data = process_email_simple(email_data)

            if not processed_data:
                continue

            processed_emails.append(processed_data)

        # Save processed emails
        save_emails(processed_emails)

        processing_method = "LLM-powered" if use_llm else "Simple"
        return jsonify({
            'success': True,
            'message': f'Processed {len(processed_emails)} emails using {processing_method} analysis',
            'emails': processed_emails,
            'method': processing_method
        })

    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return jsonify({
            'success': False,
            'message': f'Error processing emails: {str(e)}'
        }), 500


@app.route('/api/emails')
def get_emails():
    """Get list of processed email headings."""
    try:
        emails = load_emails()
        email_list = []

        for email in emails:
            email_list.append({
                'id': email['id'],
                'subject': email['subject'],
                'is_important': email['is_important'],
                'has_deadline': email['has_deadline'],
                'categories': email['categories'],
                'processed_at': email['processed_at']
            })

        return jsonify({
            'success': True,
            'emails': email_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading emails: {str(e)}'
        }), 500


@app.route('/api/email/<email_id>')
def get_email_summary(email_id):
    """Get detailed summary for a specific email."""
    try:
        emails = load_emails()
        email = next((e for e in emails if e['id'] == email_id), None)

        if not email:
            return jsonify({
                'success': False,
                'message': 'Email not found'
            }), 404

        return jsonify({
            'success': True,
            'email': email
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading email: {str(e)}'
        }), 500


def open_browser():
    """Open the web browser after a short delay."""
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:5000')


if __name__ == '__main__':
    print("🚀 Starting Gmail Intelligent Processor (Simple Version)...")
    print("📧 This version uses simple text processing")
    print("🌐 Opening web browser...")

    # Open browser in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

    # Run Flask app
    app.run(debug=True, use_reloader=False)
