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

from .ai_models import AIContext, AIRole, TemporalRule, EmailIntent, AIResponse
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
            role_name = getattr(ai_context, 'name', None) or getattr(ai_context, 'role', 'AI Assistant')
            return f"Thank you for your email. I'll get back to you soon.\n\nBest regards,\n{role_name}"
    
    def _build_system_prompt(self, ai_context: AIContext) -> str:
        """Build system prompt for intent analysis"""

        # Get role name (AIRole uses 'name', AIContext uses 'role')
        role_name = getattr(ai_context, 'name', None) or getattr(ai_context, 'role', 'AI Assistant')

        # Get topics that this role CAN respond to
        can_respond_topics = ai_context.can_respond_topics.strip() if ai_context.can_respond_topics else ""
        cannot_respond_topics = ai_context.cannot_respond_topics.strip() if ai_context.cannot_respond_topics else ""

        # Build topics section
        topics_section = ""
        if can_respond_topics:
            topics_list = "\n".join([f"  - {t.strip()}" for t in can_respond_topics.split('\n') if t.strip()])
            topics_section += f"""
THIS ROLE CAN RESPOND TO THESE TOPICS:
{topics_list}

Only respond to emails about these topics. If email is NOT about one of these topics, MUST escalate."""

        if cannot_respond_topics:
            escalate_list = "\n".join([f"  - {t.strip()}" for t in cannot_respond_topics.split('\n') if t.strip()])
            topics_section += f"""

THIS ROLE MUST ESCALATE THESE TOPICS (do not respond):
{escalate_list}"""

        prompt = f"""You are an AI email analyzer for: {role_name}

CONTEXT:
{ai_context.context_description}
{topics_section}

IMPORTANT: Check if email is about allowed topics BEFORE deciding to respond.
If the email topic is NOT in the list of topics this role can respond to, you MUST escalate.

Return ONLY valid JSON with these fields:
- intent_type: Type of email (exam_info, schedule_inquiry, academic_question, personal_matter, administrative, unclear)
- confidence: Your confidence level (0.0 to 1.0)
- decision: Either "respond" (if topic is allowed), "escalate" (if topic not allowed or sensitive), or "ignore" (if spam)
- reason: Brief explanation of your decision

EXAMPLE:
{{"intent_type": "exam_info", "confidence": 0.9, "decision": "respond", "reason": "Student asking about exam dates - this is in allowed topics"}}

CRITICAL RULES:
1. If email is about a topic NOT in the allowed list → decision MUST be "escalate"
2. If email is about a topic in the "must escalate" list → decision MUST be "escalate"
3. Only decide "respond" if topic matches allowed topics AND confidence > 0.7"""

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

        # Get role name (AIRole uses 'name', AIContext uses 'role')
        role_name = getattr(ai_context, 'name', None) or getattr(ai_context, 'role', 'AI Assistant')

        rule_info = ""
        if matched_rule:
            rule_info = f"""
SPECIFIC RULE MATCHED: {matched_rule.name}
RULE DESCRIPTION: {matched_rule.description}
RULE TEMPLATE: {matched_rule.response_template}
"""

        return f"""You are an AI assistant responding to emails on behalf of:

ROLE: {role_name}
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

        Uses the currently active AIRole if available, falls back to AIContext for backward compatibility.

        Returns:
            Tuple of (EmailIntent, AIResponse or None)
        """
        logger.info(f"Processing email: {email.subject[:50]} from {email.sender}")

        try:
            # Get user (support both email_account and legacy gmail_account)
            user = email.email_account.user if email.email_account else email.gmail_account.user

            # Try to get active AIRole (new system)
            ai_context = AIRole.get_active_role(user)

            if ai_context is None:
                raise AIContext.DoesNotExist("No active AI role or context")

            logger.info(f"Using {'AIRole' if isinstance(ai_context, AIRole) else 'AIContext'} for user {user.username}")

        except (AIContext.DoesNotExist, AIRole.DoesNotExist):
            logger.warning(f"No active AI role or context for user {user.username}")
            # Create basic intent for unprocessed email
            intent = EmailIntent.objects.create(
                email=email,
                intent_type='unclear',
                confidence_score=0.0,
                ai_decision='escalate',
                decision_reason='No AI role or context configured',
                processing_time_ms=0
            )
            return intent, None
        except Exception as e:
            logger.error(f"Error getting AI context for email {email.id}: {e}")
            intent = EmailIntent.objects.create(
                email=email,
                intent_type='unclear',
                confidence_score=0.0,
                ai_decision='escalate',
                decision_reason=f'Error loading AI configuration: {str(e)}',
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
                # Always create as 'pending_approval' first
                # The scheduler will decide to send automatically if auto_send is enabled
                ai_response = AIResponse.objects.create(
                    email_intent=intent,
                    response_text=response_text,
                    response_subject=f"Re: {email.subject}",
                    status='pending_approval'
                )
                
                logger.info(f"Response generated for email: {email.subject[:50]}")
                
            except Exception as e:
                logger.error(f"Error generating response for email {email.id}: {e}")
        
        return intent, ai_response
    
    def _find_matching_rule(self, email: Email, ai_context, analysis: Dict) -> TemporalRule:
        """
        Find matching temporal rule for the email.

        Supports both AIRole and AIContext (backward compatibility).
        """

        now = django_timezone.now()

        # Build query based on context type (AIRole or AIContext)
        if isinstance(ai_context, AIRole):
            active_rules = TemporalRule.objects.filter(
                ai_role=ai_context,
                status='active',
                start_date__lte=now,
                end_date__gte=now
            ).order_by('-priority')
        else:
            # Legacy AIContext
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