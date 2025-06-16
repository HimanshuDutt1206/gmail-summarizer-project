import os
from dotenv import load_dotenv
import ollama
import re
import time
import json

# Load environment variables
load_dotenv()


class LLMService:
    def __init__(self):
        self.client = ollama.Client()
        self.model_name = "mistral:7b"  # Default model

        # Try to connect to Ollama and verify model availability
        try:
            models = self.client.list()
            available_models = [model['name'] for model in models['models']]
            print(f"[DEBUG] Available Ollama models: {available_models}")

            if self.model_name in available_models:
                print(
                    f"[DEBUG] Successfully connected to Ollama with model: {self.model_name}")
                # Test the model with a simple call
                test_response = self.client.chat(model=self.model_name, messages=[
                    {'role': 'user', 'content': 'Hello, respond with just "OK"'}
                ])
                if test_response:
                    print("[DEBUG] Ollama model test successful")
                    self.is_available = True
                else:
                    print("[DEBUG] Ollama model test failed")
                    self.is_available = False
            else:
                print(
                    f"[DEBUG] Model {self.model_name} not available. Available models: {available_models}")
                if available_models:
                    self.model_name = available_models[0]
                    print(
                        f"[DEBUG] Using first available model: {self.model_name}")
                    self.is_available = True
                else:
                    print("[DEBUG] No models available in Ollama")
                    self.is_available = False

        except Exception as e:
            print(f"[DEBUG] Failed to connect to Ollama: {e}")
            self.is_available = False

    def _call_ollama(self, prompt, max_retries=3):
        """Make a call to Ollama with retry logic."""
        if not self.is_available:
            return None

        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] Calling Ollama API (attempt {attempt + 1})")

                response = self.client.chat(
                    model=self.model_name,
                    messages=[
                        {'role': 'system', 'content': 'You are an email classifier. Always respond with valid JSON only. Choose exactly ONE importance level.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    options={
                        'temperature': 0.05,  # Even lower temperature for consistency
                        'top_p': 0.7,
                        'num_predict': 600,  # Shorter responses
                        'repeat_penalty': 1.2,
                        # Stop at explanations
                        'stop': ['\n\n', '```', 'Note:', 'Remember:'],
                    }
                )

                if response and 'message' in response and 'content' in response['message']:
                    result = response['message']['content'].strip()
                    print(f"[DEBUG] Ollama response: {result[:100]}...")
                    return result
                else:
                    print("[DEBUG] Ollama returned empty response")
                    return None

            except Exception as e:
                print(f"[DEBUG] Ollama API error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    return None

        return None

    def analyze_email_comprehensive(self, subject, content, email_metadata=None):
        """Comprehensive email analysis using Ollama for importance, categories, summary, and deadlines."""
        print(f"[DEBUG] Analyzing email comprehensively: {subject[:30]}...")

        # Clean content for better processing
        clean_content = self._clean_email_content(content)

        # Include metadata if available
        metadata_info = ""
        if email_metadata:
            if email_metadata.get('date_header'):
                metadata_info += f"\nEmail Date Header: {email_metadata['date_header']}"
            if email_metadata.get('sender'):
                metadata_info += f"\nSender: {email_metadata['sender']}"

        prompt = f"""You are an expert email classifier. Analyze this email and classify its importance level with STRICT accuracy.

EMAIL TO ANALYZE:
Subject: {subject}
Content: {clean_content}{metadata_info}

STRICT IMPORTANCE RULES:

🔴 VERY_IMPORTANT (ONLY if BOTH conditions are met):
1. Has a SPECIFIC DEADLINE (today, tomorrow, specific date/time)
2. AND requires IMPORTANT ACTION that you must complete
Examples:
- "Meeting today at 2 PM" ✅
- "Payment due tomorrow" ✅  
- "Project submission deadline June 18" ✅
- "Server down - fix immediately" ✅
- "Security breach - action required now" ✅

🟡 IMPORTANT (Information you will need later):
- Work emails with useful information (no urgent deadline)
- Meeting invitations for future dates (next week, next month)
- Booking confirmations, travel details, flight tickets
- Educational materials, course content
- Bills/invoices (not due immediately)
- Official communications from institutions
- Reservation confirmations, hotel bookings
Examples:
- "Meeting next Monday" ✅
- "Flight confirmation for next month" ✅
- "Booking confirmation 6FEMTK" ✅
- "Course materials shared" ✅
- "Invoice - due in 30 days" ✅

🟢 UNIMPORTANT (Can check at your own pace):
- Newsletters, blogs, news updates
- Social media notifications
- Non-urgent personal emails
- System notifications (non-critical)
- Automated reports
Examples:
- "Weekly newsletter" ✅
- "LinkedIn notification" ✅
- "System backup completed" ✅

🔴 SPAM (Wouldn't matter if you never saw it):
- ALL marketing emails (even from known companies)
- Promotional offers, sales, discounts
- Unsolicited advertisements
- Phishing attempts
- Any email trying to sell you something
Examples:
- "50% off sale!" ✅
- "New products available" ✅
- "Limited time offer" ✅
- "Do you play Pickleball? Check our gear" ✅
- Any email from marketing@company.com ✅

CRITICAL RULES:
- Marketing emails = SPAM (even if from legitimate companies)
- No deadline + no important action = NOT VERY_IMPORTANT
- Promotional content = SPAM regardless of sender
- Be VERY strict with VERY_IMPORTANT classification

Respond ONLY with valid JSON:

{{
    "importance_level": "VERY_IMPORTANT|IMPORTANT|UNIMPORTANT|SPAM",
    "summary": "DETAILED summary including ALL specific information: exact dates, times, meeting IDs, phone numbers, confirmation numbers, flight details, deadlines. Be specific and include actionable details that the user needs to know.",
    "deadlines": ["Extract SPECIFIC dates and times only - use actual dates, not 'today'"],
    "has_deadline": true/false,
    "reasoning": "Explain WHY you chose this level based on the STRICT rules above",
    "important_links": ["Meeting join URLs, booking links, action URLs only"],
    "attachments_mentioned": ["Important files mentioned"]
}}

SUMMARY REQUIREMENTS:
- Include SPECIFIC dates and times (not "today" or "specified time")
- Include meeting IDs, passcodes, phone numbers
- Include confirmation numbers, flight numbers, booking details
- Include exact deadlines and what needs to be done
- Be detailed but concise (2-3 sentences max)
- Focus on actionable information the user needs

Remember: Choose ONLY ONE importance level. Be EXTREMELY strict with classifications."""

        result = self._call_ollama(prompt)

        if result:
            try:
                # Clean up the response to fix common JSON issues
                cleaned_result = result.strip()

                # Fix common escape sequence issues
                cleaned_result = cleaned_result.replace('\\_', '_')
                cleaned_result = cleaned_result.replace('\\n', ' ')

                # Find JSON boundaries
                json_start = cleaned_result.find('{')
                json_end = cleaned_result.rfind('}') + 1

                if json_start != -1 and json_end != 0:
                    json_str = cleaned_result[json_start:json_end]

                    # Additional cleanup for common issues
                    json_str = json_str.replace('\n', ' ')  # Remove newlines
                    # Normalize whitespace
                    json_str = re.sub(r'\s+', ' ', json_str)

                    analysis = json.loads(json_str)

                    print(
                        f"[DEBUG] Ollama analysis successful: {analysis.get('importance_level', 'Unknown')}")
                    print(
                        f"[DEBUG] Reasoning: {analysis.get('reasoning', 'No reasoning provided')}")

                    # Validate and fix importance level (ensure only one level)
                    if 'importance_level' not in analysis:
                        print("[DEBUG] Missing importance_level in response")
                        return None

                    # Fix multiple importance levels (take the first/highest priority)
                    importance = analysis['importance_level']
                    if '|' in importance:
                        levels = importance.split('|')
                        # Priority order: VERY_IMPORTANT > IMPORTANT > UNIMPORTANT > SPAM
                        if 'VERY_IMPORTANT' in levels:
                            analysis['importance_level'] = 'VERY_IMPORTANT'
                        elif 'IMPORTANT' in levels:
                            analysis['importance_level'] = 'IMPORTANT'
                        elif 'UNIMPORTANT' in levels:
                            analysis['importance_level'] = 'UNIMPORTANT'
                        else:
                            analysis['importance_level'] = 'SPAM'
                        print(
                            f"[DEBUG] Fixed multiple importance levels: {importance} → {analysis['importance_level']}")

                    return analysis
                else:
                    print("[DEBUG] Could not find JSON in Ollama response")
                    print(f"[DEBUG] Raw response: {result[:200]}...")
                    return None

            except json.JSONDecodeError as e:
                print(f"[DEBUG] Failed to parse Ollama JSON response: {e}")
                print(f"[DEBUG] Raw response: {result[:300]}...")

                # Try to extract importance level manually as fallback
                importance_match = re.search(
                    r'"importance_level":\s*"([^"]+)"', result)
                if importance_match:
                    importance = importance_match.group(1)
                    print(
                        f"[DEBUG] Extracted importance level manually: {importance}")
                    return {
                        'importance_level': importance,
                        'summary': 'Failed to parse full analysis',
                        'deadlines': [],
                        'has_deadline': False,
                        'reasoning': 'JSON parsing failed',
                        'important_links': [],
                        'attachments_mentioned': []
                    }
                return None
        else:
            print("[DEBUG] Ollama analysis failed")
            return None

    def categorize_email(self, subject, content):
        """Categorize email - now uses comprehensive analysis."""
        analysis = self.analyze_email_comprehensive(subject, content)

        if analysis and 'importance_level' in analysis:
            return [analysis['importance_level']]
        else:
            print("[DEBUG] Using fallback categorization")
            return self._simple_categorize_fallback(subject, content)

    def summarize_email(self, content):
        """Summarize email - now uses comprehensive analysis."""
        # For backward compatibility, we might be called directly
        # In that case, try to get the subject from the app flow
        analysis = self.analyze_email_comprehensive("", content)

        if analysis and 'summary' in analysis:
            return analysis['summary']
        else:
            print("[DEBUG] Using fallback summarization")
            return self._simple_summarize_fallback(content)

    def extract_deadlines(self, subject, content):
        """Extract deadlines - now uses comprehensive analysis."""
        analysis = self.analyze_email_comprehensive(subject, content)

        if analysis and 'deadlines' in analysis and analysis['deadlines']:
            deadlines = analysis['deadlines']
            print(f"[DEBUG] Ollama deadlines: {deadlines}")
            return deadlines
        else:
            print("[DEBUG] Using fallback deadline extraction")
            return self._extract_deadlines_regex(subject, content)

    def get_importance_level(self, subject, content):
        """Get importance level from comprehensive analysis."""
        analysis = self.analyze_email_comprehensive(subject, content)

        if analysis and 'importance_level' in analysis:
            return analysis['importance_level']
        else:
            # Fallback importance detection
            return self._simple_importance_fallback(subject, content)

    def _clean_email_content(self, content):
        """Clean email content for better processing."""
        if not content:
            return ""

        # Remove CSS style blocks
        content = re.sub(r'<style[^>]*>.*?</style>',
                         '', content, flags=re.DOTALL | re.IGNORECASE)

        # Remove inline CSS and style attributes
        content = re.sub(
            r'style\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)

        # Remove CSS rules that might be in the content
        content = re.sub(r'\{[^}]*\}', '', content)
        content = re.sub(r'[a-zA-Z-]+\s*:\s*[^;]+;', '', content)

        # Remove HTML tags
        content = re.sub(r'<[^>]+>', ' ', content)

        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)

        # Remove common email footers and unsubscribe links
        content = re.sub(r'unsubscribe.*?$', '', content, flags=re.IGNORECASE)
        content = re.sub(r'click here to view.*?$', '',
                         content, flags=re.IGNORECASE)

        # Remove CSS-related keywords that might leak through
        css_keywords = ['padding', 'margin', 'font-family',
                        'border', 'div', 'tbody', 'td', 'tr', 'table']
        for keyword in css_keywords:
            content = re.sub(
                rf'\b{keyword}\b[^a-zA-Z]*', '', content, flags=re.IGNORECASE)

        return content.strip()

    def _extract_deadlines_regex(self, subject, content):
        """Fallback regex-based deadline extraction."""
        deadlines = []
        text = (subject + " " + content).lower()

        # Common deadline patterns
        deadline_patterns = [
            r'deadline.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'due.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'by.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'before.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}).*?deadline',
            r'submit.*?by.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]

        for pattern in deadline_patterns:
            matches = re.findall(pattern, text)
            deadlines.extend(matches)

        return list(set(deadlines))  # Remove duplicates

    def _simple_categorize_fallback(self, subject, content):
        """Improved fallback categorization using strict keyword analysis."""
        text = (subject + " " + content).lower()
        print(f"[DEBUG] Using fallback categorization for: {subject[:50]}...")

        # IMPORTANT indicators (check FIRST for legitimate business emails)
        important_keywords = [
            'booking confirmation', 'flight confirmation', 'reservation confirmed',
            'ticket', 'itinerary', 'travel', 'hotel booking', 'car rental',
            'meeting', 'appointment', 'conference', 'call',
            'invoice', 'bill', 'payment', 'receipt',
            'project', 'assignment', 'course', 'materials',
            'document', 'report', 'proposal', 'visa', 'passport'
        ]

        # VERY_IMPORTANT indicators (deadline + important action)
        very_urgent_keywords = [
            'urgent', 'asap', 'emergency', 'critical', 'immediate',
            'today', 'tonight', 'this morning', 'this afternoon',
            'deadline today', 'due today', 'expires today',
            'server down', 'system failure', 'security alert',
            'action required immediately'
        ]

        # SPAM indicators (marketing/promotional) - Check AFTER important business emails
        spam_keywords = [
            # Marketing indicators (but exclude legitimate booking terms)
            'sale', 'discount', 'offer', 'deal', 'promotion', 'promo',
            'buy now', 'shop now', 'limited time offer', 'exclusive deal',
            'free shipping', 'save money', 'best price',
            # Sports/product marketing
            'play', 'gear', 'equipment', 'new products', 'collection',
            'new arrivals', 'trending', 'popular', 'bestseller',
            # Suspicious/scam
            'congratulations', 'winner', 'prize', 'lottery',
            'click here now', 'act now', 'urgent offer',
            'verify account', 'suspended account', 'inheritance'
        ]

        # UNIMPORTANT indicators (informational)
        unimportant_keywords = [
            'newsletter', 'blog', 'news', 'update', 'digest',
            'notification', 'reminder', 'summary',
            'linkedin', 'facebook', 'twitter', 'social',
            'backup completed', 'maintenance'
        ]

        # Check for IMPORTANT first (legitimate business emails)
        if any(keyword in text for keyword in important_keywords):
            print(f"[DEBUG] Classified as IMPORTANT due to business keywords")
            return ['IMPORTANT']

        # Check for VERY_IMPORTANT (urgent + deadline)
        if any(keyword in text for keyword in very_urgent_keywords):
            print(f"[DEBUG] Classified as VERY_IMPORTANT due to urgency keywords")
            return ['VERY_IMPORTANT']

        # Check for SPAM (marketing/promotional)
        if any(keyword in text for keyword in spam_keywords):
            print(f"[DEBUG] Classified as SPAM due to marketing/promotional keywords")
            return ['SPAM']

        # Check sender for marketing indicators
        if any(word in text for word in ['marketing@', 'noreply@', 'no-reply@', 'promo@']):
            print(f"[DEBUG] Classified as SPAM due to marketing sender")
            return ['SPAM']

        # Check for UNIMPORTANT (informational)
        if any(keyword in text for keyword in unimportant_keywords):
            print(f"[DEBUG] Classified as UNIMPORTANT due to informational keywords")
            return ['UNIMPORTANT']

        # Default to UNIMPORTANT (be conservative)
        print(f"[DEBUG] No keywords matched, defaulting to UNIMPORTANT")
        return ['UNIMPORTANT']

    def _simple_summarize_fallback(self, content):
        """Simple fallback summarization."""
        if not content:
            return "No content available"

        # Take first few sentences
        sentences = content.split('.')[:3]
        summary = '. '.join(sentences).strip()

        if len(summary) > 200:
            summary = summary[:200] + "..."

        return summary or "Unable to generate summary"

    def _simple_importance_fallback(self, subject, content):
        """Improved fallback importance detection."""
        categories = self._simple_categorize_fallback(subject, content)
        return categories[0] if categories else 'IMPORTANT'
