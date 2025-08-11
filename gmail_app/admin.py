from django.contrib import admin
from .models import GmailAccount, Email


@admin.register(GmailAccount)
class GmailAccountAdmin(admin.ModelAdmin):
    list_display = ['email', 'user', 'created_at']
    readonly_fields = ['access_token', 'refresh_token']


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ['subject', 'sender', 'received_date', 'is_read']
    list_filter = ['is_read', 'is_important', 'received_date']
    search_fields = ['subject', 'sender']
    readonly_fields = ['gmail_id', 'thread_id']