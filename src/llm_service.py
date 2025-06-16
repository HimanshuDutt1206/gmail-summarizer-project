import os
from dotenv import load_dotenv
from groq import Groq
import re
import json

# Load environment variables
load_dotenv()


class LLMService:
    def __init__(self):
        # Initialize Groq client
        api_key = os.getenv('GROQ_API_KEY')

        if not api_key:
            print("[ERROR] GROQ_API_KEY not found in environment variables!")
            print("[INFO] Please add your Groq API key to the .env file")
            self.is_available = False
            return

        try:
            self.client = Groq(api_key=api_key)
            # Use Llama 3 70B - best model for email analysis
            self.model_name = "llama3-70b-8192"

            # Test the connection
            print("[DEBUG] Testing Groq connection...")
            test_response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": "Hello, respond with just 'OK'"}],
                max_tokens=10,
                temperature=0.1
            )

            if test_response.choices[0].message.content:
                print(
                    f"[DEBUG] ✅ Groq connected successfully with {self.model_name}")
                self.is_available = True
            else:
                print("[DEBUG] ❌ Groq test failed")
                self.is_available = False

        except Exception as e:
            print(f"[ERROR] Failed to connect to Groq: {e}")
            print("[INFO] Check your API key and internet connection")
            self.is_available = False

    def _call_groq(self, prompt, max_tokens=800, temperature=0.1):
        """Make a call to Groq API with error handling."""
        if not self.is_available:
            return None

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert email classifier. Always respond with valid JSON only. Be precise and consistent with classifications."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9
            )

            result = response.choices[0].message.content.strip()
            print(f"[DEBUG] Groq API call successful")
            return result

        except Exception as e:
            print(f"[ERROR] Groq API call failed: {e}")
            return None

    def analyze_email_comprehensive(self, subject, content, email_metadata=None):
        """Comprehensive email analysis using Groq Llama 3 70B."""
        print(f"[DEBUG] Analyzing email with Groq: {subject[:50]}...")

        # Clean content for better processing
        clean_content = self._clean_email_content(content)

        # Include metadata if available
        metadata_info = ""
        if email_metadata:
            if email_metadata.get('date_header'):
                metadata_info += f"\nEmail Date: {email_metadata['date_header']}"
            if email_metadata.get('sender'):
                metadata_info += f"\nSender: {email_metadata['sender']}"

        prompt = f"""Analyze this email and provide a comprehensive classification. Be extremely strict with importance levels.

EMAIL TO ANALYZE:
Subject: {subject}
Content: {clean_content}{metadata_info}

STRICT CLASSIFICATION RULES:

🔴 VERY_IMPORTANT (Only if BOTH conditions are met):
1. Has a SPECIFIC DEADLINE (today, tomorrow, exact date/time)
2. AND requires CRITICAL ACTION from the recipient
Examples: "Meeting today at 2PM", "Payment due tomorrow", "Server down - fix now"

🟡 IMPORTANT (Useful information you'll need later):
- Meeting invitations (future dates)
- Booking confirmations, travel details
- Work assignments, course materials
- Bills/invoices (not due immediately)
- Official communications
Examples: "Meeting next Monday", "Flight confirmation", "Invoice due in 30 days"

🟢 UNIMPORTANT (Informational, no action needed):
- Newsletters, news updates
- Social media notifications
- System notifications (non-critical)
- Personal casual emails
Examples: "Weekly newsletter", "LinkedIn notification"

🔴 SPAM (Marketing/promotional content):
- ALL marketing emails (even from known companies)
- Sales, promotions, discounts
- Unsolicited advertisements
Examples: "50% off sale", "New products available", "Limited offer"

RESPONSE FORMAT - Return ONLY valid JSON:
{{
    "importance_level": "VERY_IMPORTANT|IMPORTANT|UNIMPORTANT|SPAM",
    "summary": "Detailed summary with specific dates, times, numbers, IDs, and actionable information. Include exact details the user needs to know.",
    "deadlines": ["Extract specific dates/times only - use actual dates"],
    "has_deadline": true/false,
    "reasoning": "Brief explanation for the classification choice",
    "important_links": ["Meeting URLs, booking links, action URLs only"],
    "attachments_mentioned": ["Important files or documents mentioned in content"]
}}

Be extremely precise with importance levels. Marketing emails are always SPAM regardless of sender."""

        result = self._call_groq(prompt, max_tokens=1000, temperature=0.05)

        if result:
            try:
                # Clean up response and extract JSON
                cleaned_result = result.strip()

                # Find JSON boundaries
                json_start = cleaned_result.find('{')
                json_end = cleaned_result.rfind('}') + 1

                if json_start != -1 and json_end > json_start:
                    json_str = cleaned_result[json_start:json_end]
                    analysis = json.loads(json_str)

                    # Validate required fields
                    required_fields = ['importance_level',
                                       'summary', 'deadlines', 'has_deadline']
                    if all(field in analysis for field in required_fields):
                        print(
                            f"[DEBUG] ✅ Analysis successful: {analysis['importance_level']}")
                        print(
                            f"[DEBUG] Summary: {analysis['summary'][:100]}...")
                        return analysis
                    else:
                        print("[DEBUG] ❌ Missing required fields in response")
                        return None
                else:
                    print("[DEBUG] ❌ No valid JSON found in response")
                    return None

            except json.JSONDecodeError as e:
                print(f"[DEBUG] ❌ JSON parsing failed: {e}")
                print(f"[DEBUG] Raw response: {result[:200]}...")
                return None

        print("[DEBUG] ❌ Groq analysis failed")
        return None

    def categorize_email(self, subject, content):
        """Categorize email using comprehensive analysis."""
        analysis = self.analyze_email_comprehensive(subject, content)

        if analysis and 'importance_level' in analysis:
            return [analysis['importance_level']]
        else:
            print("[DEBUG] Using fallback categorization")
            return self._simple_categorize_fallback(subject, content)

    def summarize_email(self, content):
        """Summarize email using comprehensive analysis."""
        analysis = self.analyze_email_comprehensive("", content)

        if analysis and 'summary' in analysis:
            return analysis['summary']
        else:
            print("[DEBUG] Using fallback summarization")
            return self._simple_summarize_fallback(content)

    def extract_deadlines(self, subject, content):
        """Extract deadlines using comprehensive analysis."""
        analysis = self.analyze_email_comprehensive(subject, content)

        if analysis and 'deadlines' in analysis and analysis['deadlines']:
            deadlines = analysis['deadlines']
            print(f"[DEBUG] Groq deadlines: {deadlines}")
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
            return self._simple_importance_fallback(subject, content)

    def _clean_email_content(self, content):
        """Clean email content for better processing."""
        if not content:
            return ""

        # Remove HTML tags
        content = re.sub(r'<[^>]+>', ' ', content)

        # Remove CSS style blocks and inline styles
        content = re.sub(r'<style[^>]*>.*?</style>',
                         '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(
            r'style\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)

        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)

        # Remove common email footers
        content = re.sub(r'unsubscribe.*?$', '', content, flags=re.IGNORECASE)

        # Limit length to avoid token limits
        if len(content) > 3000:
            content = content[:3000] + "..."

        return content.strip()

    def _extract_deadlines_regex(self, subject, content):
        """Fallback regex-based deadline extraction."""
        deadlines = []
        text = (subject + " " + content).lower()

        deadline_patterns = [
            r'deadline.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'due.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'by.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'before.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]

        for pattern in deadline_patterns:
            matches = re.findall(pattern, text)
            deadlines.extend(matches)

        return list(set(deadlines))

    def _simple_categorize_fallback(self, subject, content):
        """Fallback categorization when Groq is unavailable."""
        text = (subject + " " + content).lower()

        # Check for spam/marketing first
        spam_keywords = ['sale', 'discount', 'offer',
                         'deal', 'promotion', 'buy now', 'limited time']
        if any(keyword in text for keyword in spam_keywords):
            return ['SPAM']

        # Check for important business emails
        important_keywords = ['meeting', 'deadline',
                              'urgent', 'important', 'action required']
        if any(keyword in text for keyword in important_keywords):
            return ['IMPORTANT']

        # Check for very urgent
        urgent_keywords = ['today', 'asap',
                           'immediately', 'critical', 'emergency']
        if any(keyword in text for keyword in urgent_keywords):
            return ['VERY_IMPORTANT']

        return ['UNIMPORTANT']

    def _simple_summarize_fallback(self, content):
        """Simple fallback summarization."""
        if not content:
            return "No content available"

        sentences = content.split('.')[:2]
        summary = '. '.join(sentences).strip()

        if len(summary) > 200:
            summary = summary[:200] + "..."

        return summary or "Unable to generate summary"

    def _simple_importance_fallback(self, subject, content):
        """Fallback importance detection."""
        categories = self._simple_categorize_fallback(subject, content)
        return categories[0] if categories else 'UNIMPORTANT'
