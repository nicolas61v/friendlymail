from django.contrib import admin
from .models import GmailAccount, Email
from .ai_models import AIContext, TemporalRule, EmailIntent, AIResponse, AIStats


@admin.register(GmailAccount)
class GmailAccountAdmin(admin.ModelAdmin):
    list_display = ['email', 'user', 'created_at', 'updated_at']
    list_filter = ['created_at']
    readonly_fields = ['access_token', 'refresh_token']


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ['subject', 'sender', 'gmail_account', 'received_date', 'is_read']
    list_filter = ['is_read', 'is_important', 'received_date']
    search_fields = ['subject', 'sender', 'body_plain']
    readonly_fields = ['gmail_id', 'thread_id']


@admin.register(AIContext)
class AIContextAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'complexity_level', 'is_active', 'auto_send']
    list_filter = ['complexity_level', 'is_active', 'auto_send']
    search_fields = ['role', 'context_description']


@admin.register(TemporalRule)
class TemporalRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'ai_context', 'start_date', 'end_date', 'status', 'priority']
    list_filter = ['status', 'start_date', 'end_date']
    search_fields = ['name', 'keywords']


@admin.register(EmailIntent)
class EmailIntentAdmin(admin.ModelAdmin):
    list_display = ['email', 'intent_type', 'ai_decision', 'confidence_score', 'processed_at']
    list_filter = ['intent_type', 'ai_decision', 'processed_at']
    search_fields = ['email__subject', 'decision_reason']


@admin.register(AIResponse) 
class AIResponseAdmin(admin.ModelAdmin):
    list_display = ['email_intent', 'status', 'generated_at', 'sent_at']
    list_filter = ['status', 'generated_at', 'sent_at']
    search_fields = ['response_text', 'response_subject']


@admin.register(AIStats)
class AIStatsAdmin(admin.ModelAdmin):
    list_display = ['ai_context', 'date', 'emails_processed', 'responses_sent', 'avg_confidence']
    list_filter = ['date', 'ai_context']