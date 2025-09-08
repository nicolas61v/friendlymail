"""
AI Service for email intent analysis and response generation
"""
import json
import logging
import time
from typing import Dict, Any, Tuple
from datetime import datetime, timezone

from django.conf import settings
from django.utils import timezone as django_timezone
from openai import OpenAI

from .ai_models import AIContext, TemporalRule, EmailIntent, AIResponse
from .models import Email

logger = logging.getLogger('gmail_app')


class AIEmailAnalyzer:
    """AI-powered email analyzer using OpenAI"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    def analyze_email_intent(self, email: Email, ai_context: AIContext) -> Dict[str, Any]:
        """
        Analyze email intent using AI
        
        Returns:
            {
                'intent_type': str,
                'confidence': float,
                'decision': str,  # 'respond', 'escalate', 'ignore'
                'reason': str,
                'processing_time_ms': int
            }
        """
        start_time = time.time()
        
        try:
            # Prepare context for AI
            system_prompt = self._build_system_prompt(ai_context)
            user_message = self._build_user_message(email)
            
            logger.info(f"Analyzing email intent for: {email.subject[:50]}")
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Parse AI response
            ai_analysis = json.loads(response.choices[0].message.content)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            result = {
                'intent_type': ai_analysis.get('intent_type', 'unclear'),
                'confidence': ai_analysis.get('confidence', 0.0),
                'decision': ai_analysis.get('decision', 'escalate'),
                'reason': ai_analysis.get('reason', 'AI analysis unclear'),
                'processing_time_ms': processing_time
            }
            
            logger.info(f"AI Analysis completed: {result['intent_type']} ({result['confidence']:.2f}) - {result['decision']}")
            return result
            
        except Exception as e:
            logger.error(f"Error in AI email analysis: {e}")
            processing_time = int((time.time() - start_time) * 1000)
            
            # Fallback to safe escalation
            return {
                'intent_type': 'unclear',
                'confidence': 0.0,
                'decision': 'escalate',
                'reason': f'AI analysis failed: {str(e)}',
                'processing_time_ms': processing_time
            }
    
    def generate_response(self, email: Email, ai_context: AIContext, matched_rule: TemporalRule = None) -> str:
        """
        Generate AI response for an email
        
        Args:
            email: The email to respond to
            ai_context: User's AI context
            matched_rule: Specific temporal rule that matched (if any)
            
        Returns:
            Generated response text
        """
        try:
            system_prompt = self._build_response_system_prompt(ai_context, matched_rule)
            user_message = self._build_response_user_message(email)
            
            logger.info(f"Generating response for: {email.subject[:50]}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,  # Slightly more creative for responses
                max_tokens=800
            )
            
            generated_response = response.choices[0].message.content.strip()
            logger.info(f"Response generated successfully, length: {len(generated_response)}")
            
            return generated_response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            # Fallback response
            return f"Thank you for your email. I'll get back to you soon.\n\nBest regards,\n{ai_context.role}"
    
    def _build_system_prompt(self, ai_context: AIContext) -> str:
        """Build system prompt for intent analysis"""
        
        prompt = f"""You are an AI that analyzes emails for a professor.

PROFESSOR CONTEXT:
Role: {ai_context.role}
Description: {ai_context.context_description}

ANALYZE each email and return ONLY valid JSON:

For questions about exams, schedules, assignments - decision should be "respond"
For personal matters, grades, complex issues - decision should be "escalate"

EXAMPLE OUTPUT:
{{"intent_type": "exam_info", "confidence": 0.9, "decision": "respond", "reason": "Student asking about exam date"}}

INTENT OPTIONS: exam_info, schedule_inquiry, academic_question, personal_matter, administrative, unclear
DECISION OPTIONS: respond, escalate, ignore"""
        
        return prompt
    
    def _build_user_message(self, email: Email) -> str:
        """Build user message with email content"""
        
        return f"""ANALYZE THIS EMAIL:

FROM: {email.sender}
SUBJECT: {email.subject}
DATE: {email.received_date}

CONTENT:
{email.body_plain[:2000]}  

Analyze the intent and decide if this should be automatically responded to or escalated."""
    
    def _build_response_system_prompt(self, ai_context: AIContext, matched_rule: TemporalRule = None) -> str:
        """Build system prompt for response generation"""
        
        rule_info = ""
        if matched_rule:
            rule_info = f"""
SPECIFIC RULE MATCHED: {matched_rule.name}
RULE DESCRIPTION: {matched_rule.description}
RULE TEMPLATE: {matched_rule.response_template}
"""
        
        return f"""You are an AI assistant responding to emails on behalf of:

ROLE: {ai_context.role}
CONTEXT: {ai_context.context_description}

{rule_info}

GUIDELINES:
- Be helpful, professional, and concise
- Use the information provided in the context
- If a specific rule template is provided, use it as a base but adapt to the specific question
- Sign with the role name
- Keep responses under 200 words unless more detail is needed
- Be friendly but professional

Generate a helpful response to the email."""
    
    def _build_response_user_message(self, email: Email) -> str:
        """Build user message for response generation"""
        
        return f"""Generate a response to this email:

FROM: {email.sender}
SUBJECT: {email.subject}

CONTENT:
{email.body_plain[:1500]}

Generate an appropriate response."""


class EmailAIProcessor:
    """Main processor for AI email handling"""
    
    def __init__(self):
        self.analyzer = AIEmailAnalyzer()
    
    def process_email(self, email: Email) -> Tuple[EmailIntent, AIResponse]:
        """
        Process a single email through the AI pipeline
        
        Returns:
            Tuple of (EmailIntent, AIResponse or None)
        """
        logger.info(f"Processing email: {email.subject[:50]} from {email.sender}")
        
        try:
            # Get user's AI context
            ai_context = AIContext.objects.get(user=email.gmail_account.user, is_active=True)
        except AIContext.DoesNotExist:
            logger.warning(f"No active AI context for user {email.gmail_account.user.username}")
            # Create basic intent for unprocessed email
            intent = EmailIntent.objects.create(
                email=email,
                intent_type='unclear',
                confidence_score=0.0,
                ai_decision='escalate',
                decision_reason='No AI context configured',
                processing_time_ms=0
            )
            return intent, None
        
        # Check if email domain is allowed
        if ai_context.allowed_domains:
            allowed_domains = [d.strip() for d in ai_context.allowed_domains.split('\n') if d.strip()]
            sender_domain = email.sender.split('@')[-1] if '@' in email.sender else ''
            
            if not any(domain.replace('@', '') in sender_domain for domain in allowed_domains):
                logger.info(f"Email from {email.sender} not in allowed domains, escalating")
                intent = EmailIntent.objects.create(
                    email=email,
                    intent_type='administrative',
                    confidence_score=1.0,
                    ai_decision='escalate',
                    decision_reason='Sender domain not in allowed list',
                    processing_time_ms=0
                )
                return intent, None
        
        # Analyze email intent
        analysis = self.analyzer.analyze_email_intent(email, ai_context)
        
        # Check for matching temporal rules
        matched_rule = self._find_matching_rule(email, ai_context, analysis)
        
        # Create EmailIntent record
        intent = EmailIntent.objects.create(
            email=email,
            intent_type=analysis['intent_type'],
            confidence_score=analysis['confidence'],
            ai_decision=analysis['decision'],
            decision_reason=analysis['reason'],
            matched_rule=matched_rule,
            processing_time_ms=analysis['processing_time_ms']
        )
        
        # Generate response if decision is 'respond'
        ai_response = None
        if analysis['decision'] == 'respond':
            try:
                response_text = self.analyzer.generate_response(email, ai_context, matched_rule)
                
                # Create AIResponse record
                ai_response = AIResponse.objects.create(
                    email_intent=intent,
                    response_text=response_text,
                    response_subject=f"Re: {email.subject}",
                    status='pending_approval' if not ai_context.auto_send else 'approved'
                )
                
                logger.info(f"Response generated for email: {email.subject[:50]}")
                
            except Exception as e:
                logger.error(f"Error generating response for email {email.id}: {e}")
        
        return intent, ai_response
    
    def _find_matching_rule(self, email: Email, ai_context: AIContext, analysis: Dict) -> TemporalRule:
        """Find matching temporal rule for the email"""
        
        now = django_timezone.now()
        
        # Get active rules for this context
        active_rules = TemporalRule.objects.filter(
            ai_context=ai_context,
            status='active',
            start_date__lte=now,
            end_date__gte=now
        ).order_by('-priority')
        
        for rule in active_rules:
            # Check if email content matches rule keywords
            email_content = f"{email.subject} {email.body_plain}".lower()
            keywords = [kw.strip().lower() for kw in rule.keywords.split(',') if kw.strip()]
            
            if any(keyword in email_content for keyword in keywords):
                logger.info(f"Email matched temporal rule: {rule.name}")
                return rule
        
        return None