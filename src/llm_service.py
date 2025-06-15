import os
from dotenv import load_dotenv
import google.generativeai as genai
import re
import time
import json

# Load environment variables
load_dotenv()


class LLMService:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Try different model names to find what works
            model_names = ['gemini-1.5-flash',
                           'gemini-pro', 'models/gemini-pro']
            self.model = None

            for model_name in model_names:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    # Test the model with a simple call
                    test_response = self.model.generate_content("Hello")
                    if test_response:
                        print(
                            f"[DEBUG] Successfully initialized Google Gemini with model: {model_name}")
                        break
                except Exception as e:
                    print(f"[DEBUG] Model {model_name} failed: {str(e)[:100]}")
                    continue

            if not self.model:
                print("[DEBUG] All Gemini models failed, will use fallback methods")
        else:
            print("[DEBUG] No Gemini API key found, will use fallback methods")
            self.model = None

    def _call_gemini(self, prompt, max_retries=3):
        """Make a call to Gemini API with retry logic."""
        if not self.model:
            return None

        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] Calling Gemini API (attempt {attempt + 1})")
                response = self.model.generate_content(prompt)

                if response and response.text:
                    result = response.text.strip()
                    print(f"[DEBUG] Gemini response: {result[:100]}...")
                    return result
                else:
                    print("[DEBUG] Gemini returned empty response")
                    return None

            except Exception as e:
                print(f"[DEBUG] Gemini API error: {e}")
                if "quota" in str(e).lower() or "limit" in str(e).lower():
                    print("[DEBUG] Rate limited, waiting 10 seconds...")
                    time.sleep(10)
                elif attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    return None

        return None

    def analyze_email_comprehensive(self, subject, content):
        """Comprehensive email analysis using Gemini for importance, categories, summary, and deadlines."""
        print(f"[DEBUG] Analyzing email comprehensively: {subject[:30]}...")

        # Clean content for better processing
        clean_content = self._clean_email_content(content)

        prompt = f"""
Analyze this email and provide a comprehensive analysis. Respond in JSON format exactly as shown:

Email Subject: {subject}
Email Content: {clean_content}

Provide analysis in this exact JSON format:
{{
    "importance_level": "VERY_IMPORTANT|IMPORTANT|UNIMPORTANT|SPAM",
    "summary": "2-3 sentence summary of the email's main points and purpose",
    "deadlines": ["list of specific deadlines or dates found", "e.g. June 18, 2025", "tomorrow by 5pm"],
    "has_deadline": true/false,
    "reasoning": "Brief explanation of why this importance level was assigned"
}}

Importance Guidelines:
- VERY_IMPORTANT: Urgent deadlines, critical business matters, emergency situations
- IMPORTANT: Work tasks, meetings, deadlines, bills, official communications
- UNIMPORTANT: Newsletters, notifications, non-urgent personal emails
- SPAM: Promotional emails, advertisements, suspicious content

Focus on extracting actual dates, deadlines, and time-sensitive information. Be specific about deadlines.
"""

        result = self._call_gemini(prompt)

        if result:
            try:
                # Try to parse JSON response
                # Clean up the response in case it has extra text
                json_start = result.find('{')
                json_end = result.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    json_str = result[json_start:json_end]
                    analysis = json.loads(json_str)

                    print(
                        f"[DEBUG] Gemini analysis successful: {analysis['importance_level']}")
                    return analysis
                else:
                    print("[DEBUG] Could not find JSON in Gemini response")
                    return None

            except json.JSONDecodeError as e:
                print(f"[DEBUG] Failed to parse Gemini JSON response: {e}")
                print(f"[DEBUG] Raw response: {result}")
                return None
        else:
            print("[DEBUG] Gemini analysis failed")
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
            print(f"[DEBUG] Gemini deadlines: {deadlines}")
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
            text = f"{subject} {content}".lower()
            if any(word in text for word in ['urgent', 'critical', 'emergency', 'asap', 'immediate']):
                return 'VERY_IMPORTANT'
            elif any(word in text for word in ['important', 'deadline', 'meeting', 'due', 'action required']):
                return 'IMPORTANT'
            elif any(word in text for word in ['sale', 'offer', 'marketing', 'unsubscribe', 'promotion']):
                return 'SPAM'
            else:
                return 'UNIMPORTANT'

    def _clean_email_content(self, content):
        """Clean email content for better processing."""
        # Remove common email artifacts
        content = re.sub(r'On .* wrote:', '', content)
        content = re.sub(r'From:.*?Subject:', '', content, flags=re.DOTALL)
        content = re.sub(r'http[s]?://\S+', '[URL]', content)
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()

        return content[:2000]  # Limit length for API

    def _extract_deadlines_regex(self, subject, content):
        """Extract deadlines using regex as fallback."""
        text = f"{subject} {content}"
        deadlines = []

        # More comprehensive date patterns
        date_patterns = [
            # Specific dates
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY
            # Month DD, YYYY
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{2,4}\b',
            # Mon DD, YYYY
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{2,4}\b',
            # 18th June 2025
            r'\b\d{1,2}(?:st|nd|rd|th)\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4}\b',
            # Relative dates with context
            r'\b(?:due|deadline|by|before|until|submit by)\s+(?:tomorrow|today|tonight|this week|next week|end of week)\b',
            # by 18th June
            r'\b(?:due|deadline|by|before|until|submit by)\s+\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\b',
            # Standalone relative dates when in context of deadlines
            r'\b(?:tomorrow|today|tonight|this week|next week|end of week)\b',
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            deadlines.extend(matches)

        # Clean up and deduplicate
        cleaned_deadlines = []
        for deadline in deadlines:
            deadline = deadline.strip()
            if deadline and len(deadline) > 2:  # Filter out very short matches
                cleaned_deadlines.append(deadline)

        deadlines = list(set(cleaned_deadlines))[:5]
        print(f"[DEBUG] Regex deadlines: {deadlines}")
        return deadlines

    def _simple_categorize_fallback(self, subject, content):
        """Fallback categorization when API fails."""
        text = f"{subject} {content}".lower()

        # Simple importance-based categorization
        if any(word in text for word in ['urgent', 'critical', 'emergency', 'asap', 'immediate', 'action required']):
            return ['VERY_IMPORTANT']
        elif any(word in text for word in ['important', 'deadline', 'meeting', 'due', 'project', 'work', 'business']):
            return ['IMPORTANT']
        elif any(word in text for word in ['sale', 'offer', 'discount', 'promo', 'marketing', 'unsubscribe', 'advertisement']):
            return ['SPAM']
        else:
            return ['UNIMPORTANT']

    def _simple_summarize_fallback(self, content):
        """Improved fallback summarization."""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip()
                     for s in sentences if s.strip() and len(s.strip()) > 10]

        if not sentences:
            return "Unable to generate summary from email content."

        if len(sentences) == 1:
            summary = sentences[0]
        elif len(sentences) == 2:
            summary = f"{sentences[0]}. {sentences[1]}"
        else:
            # First + important middle + last sentence
            first = sentences[0]
            last = sentences[-1]

            important_keywords = ['important', 'urgent',
                                  'need', 'require', 'please', 'action', 'deadline']
            important_sentence = None

            for sentence in sentences[1:-1]:
                if any(keyword in sentence.lower() for keyword in important_keywords):
                    important_sentence = sentence
                    break

            if important_sentence:
                summary = f"{first}. {important_sentence}. {last}"
            else:
                summary = f"{first}. {last}"

        if len(summary) > 300:
            summary = summary[:297] + "..."

        return summary
