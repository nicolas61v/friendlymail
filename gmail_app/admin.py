from django.contrib import admin
from .models import EmailAccount, GmailAccount, Email
from .ai_models import TemporalRule, EmailIntent, AIResponse


@admin.register(EmailAccount)
class EmailAccountAdmin(admin.ModelAdmin):
    list_display = ['email', 'provider', 'user', 'is_active', 'created_at']
    list_filter = ['provider', 'is_active', 'created_at']
    readonly_fields = ['access_token', 'refresh_token']
    search_fields = ['email', 'user__username']


@admin.register(GmailAccount)
class GmailAccountAdmin(admin.ModelAdmin):
    list_display = ['email', 'user', 'created_at', 'updated_at']
    list_filter = ['created_at']
    readonly_fields = ['access_token', 'refresh_token']


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ['subject', 'sender', 'email_account', 'received_date', 'is_read']
    list_filter = ['is_read', 'is_important', 'received_date']
    search_fields = ['subject', 'sender', 'body_plain']
    readonly_fields = ['provider_id', 'thread_id', 'created_at']

    def get_queryset(self, request):
        # Optimize with select_related
        return super().get_queryset(request).select_related('email_account', 'gmail_account')


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