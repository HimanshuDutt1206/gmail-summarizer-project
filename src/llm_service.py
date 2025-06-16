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

    def analyze_email_comprehensive(self, subject, content, email_metadata=None):
        """Comprehensive email analysis using Gemini for importance, categories, summary, and deadlines."""
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

        prompt = f"""
You are analyzing an email to help someone quickly understand what it's about while scanning their unread emails. The entire email content is provided below.

Email Subject: {subject}
Email Content: {clean_content}{metadata_info}

Create a clear, detailed summary that includes ALL important information while removing useless details. Respond in this exact JSON format:

{{
    "importance_level": "VERY_IMPORTANT|IMPORTANT|UNIMPORTANT|SPAM",
    "summary": "Clear, detailed summary that includes all critical information: dates, times, meeting IDs, reference numbers, phone numbers, deadlines. Remove all fluff, disclaimers, legal text, and technical details. Focus only on what the user needs to know and do.",
    "deadlines": ["list of specific deadlines or dates found - include exact dates and times"],
    "has_deadline": true/false,
    "reasoning": "Brief explanation of importance level",
    "important_links": ["ONLY include URLs that are directly actionable for the user - primary meeting join links, booking management links, direct download links. Skip: legal policies, contact pages, company logos, promotional links, help pages"],
    "attachments_mentioned": ["ONLY include documents/files that the user needs to know about - actual attachments, referenced documents, materials to review. Skip: company logos, email signatures, promotional images"]
}}

Summary Guidelines:
- Include ALL critical details but remove useless information
- For meetings: Include date/time (or state if missing), meeting ID, passcode, dial-in number
- For bookings: Include confirmation number, dates, key details
- For deadlines: Include exact date/time and what needs to be done
- For documents: Mention what documents are included/referenced
- Skip: Legal disclaimers, privacy policies, unsubscribe links, company signatures, promotional text
- Skip: Technical details like "this email is in HTML format"
- Skip: Generic phrases like "please find attached" or "hope this email finds you well"
- Focus on: What is this about? What do I need to do? When? How?

Link Selection Guidelines:
- Only include links that are directly actionable or useful to the user
- For meetings: include the main join link, skip legal/policy links
- For bookings: include confirmation/management links, skip promotional links
- For resources: include direct download/access links, skip company homepages
- Skip: contact pages, legal policies, company logos, tracking URLs, promotional content

Importance Guidelines:
- VERY_IMPORTANT: Urgent deadlines, critical business matters, emergencies
- IMPORTANT: Work tasks, meetings, deadlines, bills, official communications, bookings
- UNIMPORTANT: Newsletters, notifications, non-urgent personal emails
- SPAM: Promotional emails, advertisements, suspicious content

Extract all dates, deadlines, and time-sensitive information. Include important URLs and document references.
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
        """Minimal cleaning - send entire email content to LLM."""
        # Only basic whitespace cleanup - let LLM handle everything else
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()

        # Send entire content - no truncation, let LLM decide what's important
        return content

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
