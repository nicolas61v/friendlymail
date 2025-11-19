"""
AI-powered email assistant models
"""
from django.db import models
from django.contrib.auth.models import User
from .models import Email


class AIContext(models.Model):
    """
    DEPRECATED: User's AI context configuration
    Use AIRole instead for multiple roles support.
    This model is kept for backward compatibility.
    """

    COMPLEXITY_CHOICES = [
        ('simple', 'Simple - Basic context only'),
        ('medium', 'Medium - Context + filters + keywords'),
        ('advanced', 'Advanced - Full customization')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Basic Info
    role = models.CharField(max_length=100, help_text="e.g., 'Professor at EAFIT', 'Tech Support Manager'")
    context_description = models.TextField(help_text="Describe your role and what you do")

    # Complexity level
    complexity_level = models.CharField(max_length=20, choices=COMPLEXITY_CHOICES, default='simple')

    # What AI CAN respond to
    can_respond_topics = models.TextField(
        help_text="Topics/questions AI can answer (one per line)",
        blank=True
    )

    # What AI should NOT respond to
    cannot_respond_topics = models.TextField(
        help_text="Topics AI should escalate to you (one per line)",
        blank=True
    )

    # Email filters
    allowed_domains = models.TextField(
        help_text="Email domains to process (e.g., @eafit.edu.co, @company.com)",
        blank=True
    )

    # General settings
    is_active = models.BooleanField(default=True)
    auto_send = models.BooleanField(default=False, help_text="Auto-send responses or require approval")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class AIRole(models.Model):
    """
    NEW: AI role configuration supporting multiple roles per user

    Each user can have multiple AI roles (e.g., Professor, Coordinator, Director)
    with independent configurations, rules, and settings.

    Only ONE role per user can be active at a time (is_active=True).
    """

    COMPLEXITY_CHOICES = [
        ('simple', 'Simple - Basic context only'),
        ('medium', 'Medium - Context + filters + keywords'),
        ('advanced', 'Advanced - Full customization')
    ]

    # Relationship
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_roles')

    # Basic Info
    name = models.CharField(
        max_length=100,
        help_text="Role name (e.g., 'Professor', 'Coordinator', 'Director')"
    )
    context_description = models.TextField(
        help_text="Describe what this role does and its context"
    )

    # Role activation
    is_active = models.BooleanField(
        default=True,
        help_text="Only one role per user can be active"
    )

    # Complexity level
    complexity_level = models.CharField(
        max_length=20,
        choices=COMPLEXITY_CHOICES,
        default='simple'
    )

    # What AI CAN respond to
    can_respond_topics = models.TextField(
        help_text="Topics/questions AI can answer (one per line)",
        blank=True
    )

    # What AI should NOT respond to
    cannot_respond_topics = models.TextField(
        help_text="Topics AI should escalate to you (one per line)",
        blank=True
    )

    # Email filters
    allowed_domains = models.TextField(
        help_text="Email domains to process (e.g., @eafit.edu.co, @company.com)",
        blank=True
    )

    # Auto-send settings
    auto_send = models.BooleanField(
        default=False,
        help_text="Auto-send responses or require approval for this role"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', '-updated_at']
        # Allow multiple roles per user, but name should be unique per user
        unique_together = [['user', 'name']]
        verbose_name = "AI Role"
        verbose_name_plural = "AI Roles"

    def __str__(self):
        status = "✓ ACTIVE" if self.is_active else "inactive"
        return f"{self.user.username} - {self.name} ({status})"

    def save(self, *args, **kwargs):
        """
        Ensure only one active role per user
        """
        if self.is_active:
            # Deactivate all other roles for this user
            AIRole.objects.filter(user=self.user).exclude(pk=self.pk).update(is_active=False)

        super().save(*args, **kwargs)

    @classmethod
    def get_active_role(cls, user):
        """
        Get the currently active AI role for a user.

        Returns the active role, or None if no roles exist.
        For backward compatibility with AIContext, this can also return
        an AIContext if it exists and no AIRole exists.
        """
        # Try to get active AIRole
        try:
            return cls.objects.get(user=user, is_active=True)
        except cls.DoesNotExist:
            # Fall back to AIContext for backward compatibility
            try:
                return AIContext.objects.get(user=user, is_active=True)
            except AIContext.DoesNotExist:
                return None


class TemporalRule(models.Model):
    """Time-based rules for specific responses (per AI Role or Context)"""

    RULE_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('scheduled', 'Scheduled'),
        ('expired', 'Expired'),
        ('disabled', 'Disabled')
    ]

    # Support both AIRole (new) and AIContext (legacy) for backward compatibility
    ai_context = models.ForeignKey(
        AIContext,
        on_delete=models.CASCADE,
        related_name='temporal_rules',
        null=True,
        blank=True
    )
    ai_role = models.ForeignKey(
        AIRole,
        on_delete=models.CASCADE,
        related_name='temporal_rules',
        null=True,
        blank=True
    )
    
    # Rule identification
    name = models.CharField(max_length=200, help_text="e.g., 'Midterm Exam Info'")
    description = models.TextField(blank=True)
    
    # Time constraints
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Triggers
    keywords = models.TextField(help_text="Keywords that trigger this rule (comma-separated)")
    email_filters = models.TextField(blank=True, help_text="Additional email filters (optional)")
    
    # Response
    response_template = models.TextField(help_text="Template response for matching emails")
    
    # Settings
    status = models.CharField(max_length=20, choices=RULE_STATUS_CHOICES, default='draft')
    priority = models.IntegerField(default=1, help_text="Higher number = higher priority")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.start_date.date()} - {self.end_date.date()})"


class EmailIntent(models.Model):
    """AI-determined intent of each email"""
    
    INTENT_TYPES = [
        ('academic_question', 'Academic Question'),
        ('schedule_inquiry', 'Schedule Inquiry'), 
        ('exam_info', 'Exam Information'),
        ('assignment_info', 'Assignment Information'),
        ('technical_support', 'Technical Support'),
        ('personal_matter', 'Personal Matter'),
        ('administrative', 'Administrative'),
        ('emergency', 'Emergency'),
        ('spam', 'Spam'),
        ('unclear', 'Unclear Intent')
    ]
    
    DECISION_TYPES = [
        ('respond', 'AI Should Respond'),
        ('escalate', 'Escalate to Human'),
        ('ignore', 'Ignore (Spam)')
    ]
    
    email = models.OneToOneField(Email, on_delete=models.CASCADE)
    
    # AI Analysis
    intent_type = models.CharField(max_length=50, choices=INTENT_TYPES)
    confidence_score = models.FloatField(help_text="AI confidence (0.0 - 1.0)")
    
    # Decision
    ai_decision = models.CharField(max_length=20, choices=DECISION_TYPES)
    decision_reason = models.TextField(help_text="Why AI made this decision")
    
    # Matching rule (if any)
    matched_rule = models.ForeignKey(TemporalRule, on_delete=models.SET_NULL, null=True, blank=True)
    
    # AI processing
    processed_at = models.DateTimeField(auto_now_add=True)
    processing_time_ms = models.IntegerField(help_text="Time taken for AI analysis")
    
    def __str__(self):
        return f"{self.email.subject[:50]} - {self.intent_type} ({self.ai_decision})"


class AIResponse(models.Model):
    """AI-generated responses"""
    
    RESPONSE_STATUS = [
        ('generated', 'Generated by AI'),
        ('pending_approval', 'Pending User Approval'),
        ('approved', 'Approved by User'),
        ('rejected', 'Rejected by User'),
        ('sent', 'Sent to Recipient'),
        ('failed', 'Failed to Send')
    ]
    
    email_intent = models.OneToOneField(EmailIntent, on_delete=models.CASCADE)
    
    # Response content
    response_text = models.TextField()
    response_subject = models.CharField(max_length=200, help_text="Subject line for response")
    
    # Metadata
    status = models.CharField(max_length=20, choices=RESPONSE_STATUS, default='generated')
    generated_at = models.DateTimeField(auto_now_add=True)
    
    # User actions
    approved_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Feedback
    user_feedback = models.TextField(blank=True, help_text="User feedback on AI response quality")
    
    def __str__(self):
        return f"Response to: {self.email_intent.email.subject[:30]} - {self.status}"