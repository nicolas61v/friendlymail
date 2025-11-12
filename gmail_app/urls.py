from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # Autenticación
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Gmail
    path('connect-gmail/', views.connect_gmail, name='connect_gmail'),
    path('gmail/callback/', views.gmail_callback, name='gmail_callback'),
    path('disconnect-gmail/', views.disconnect_gmail, name='disconnect_gmail'),

    # Outlook
    path('connect-outlook/', views.connect_outlook, name='connect_outlook'),
    path('outlook/callback/', views.outlook_callback, name='outlook_callback'),
    path('disconnect-outlook/<int:account_id>/', views.disconnect_outlook, name='disconnect_outlook'),
    path('sync-outlook/', views.sync_outlook, name='sync_outlook'),

    # Multi-account management
    path('disconnect-account/<int:account_id>/', views.disconnect_email_account, name='disconnect_email_account'),
    path('sync-all/', views.sync_all_accounts, name='sync_all_accounts'),

    # Email syncing (legacy)
    path('sync-emails/', views.sync_emails, name='sync_emails'),
    path('api/sync-emails/', views.sync_emails_api, name='sync_emails_api'),

    # Email details & system
    path('email/<int:email_id>/', views.email_detail, name='email_detail'),
    path('api/logs/', views.system_logs, name='system_logs'),
    path('clear-oauth-session/', views.clear_oauth_session, name='clear_oauth_session'),
    
    # AI Configuration (Legacy - AIContext)
    path('ai-config/', views.ai_config, name='ai_config'),
    path('ai-context/save/', views.ai_context_save, name='ai_context_save'),
    path('temporal-rule/save/', views.temporal_rule_save, name='temporal_rule_save'),
    path('temporal-rule/delete/<int:rule_id>/', views.temporal_rule_delete, name='temporal_rule_delete'),

    # AI Roles (New - Multiple Roles per User)
    path('ai-roles/', views.ai_roles_list, name='ai_roles_list'),
    path('ai-roles/create/', views.ai_role_create, name='ai_role_create'),
    path('ai-roles/<int:role_id>/edit/', views.ai_role_edit, name='ai_role_edit'),
    path('ai-roles/<int:role_id>/activate/', views.ai_role_activate, name='ai_role_activate'),
    path('ai-roles/<int:role_id>/delete/', views.ai_role_delete, name='ai_role_delete'),
    path('ai-roles/<int:role_id>/rule/save/', views.ai_role_temporal_rule_save, name='ai_role_temporal_rule_save'),
    path('ai-roles/<int:role_id>/rule/<int:rule_id>/delete/', views.ai_role_temporal_rule_delete, name='ai_role_temporal_rule_delete'),

    # AI Responses
    path('ai-responses/', views.ai_responses, name='ai_responses'),
    path('response/approve/<int:response_id>/', views.approve_response, name='approve_response'),
    path('response/reject/<int:response_id>/', views.reject_response, name='reject_response'),
    path('response/resend/<int:response_id>/', views.resend_response, name='resend_response'),
    path('response/edit/<int:response_id>/', views.edit_response, name='edit_response'),
    path('api/emails-ai-status/', views.get_all_emails_with_ai_status, name='get_all_emails_with_ai_status'),
    path('process-existing-emails/', views.process_existing_emails, name='process_existing_emails'),
    path('debug/ai-status/', views.debug_ai_status, name='debug_ai_status'),
]