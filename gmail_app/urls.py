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
    path('connect-gmail/', views.connect_gmail, name='connect_gmail'),
    path('gmail/callback/', views.gmail_callback, name='gmail_callback'),
    path('sync-emails/', views.sync_emails, name='sync_emails'),
    path('api/sync-emails/', views.sync_emails_api, name='sync_emails_api'),
    path('email/<int:email_id>/', views.email_detail, name='email_detail'),
    path('api/logs/', views.system_logs, name='system_logs'),
    path('disconnect-gmail/', views.disconnect_gmail, name='disconnect_gmail'),
    path('clear-oauth-session/', views.clear_oauth_session, name='clear_oauth_session'),
    
    # AI Configuration
    path('ai-config/', views.ai_config, name='ai_config'),
    path('ai-context/save/', views.ai_context_save, name='ai_context_save'),
    path('temporal-rule/save/', views.temporal_rule_save, name='temporal_rule_save'),
    path('temporal-rule/delete/<int:rule_id>/', views.temporal_rule_delete, name='temporal_rule_delete'),
    
    # AI Responses
    path('ai-responses/', views.ai_responses, name='ai_responses'),
    path('response/approve/<int:response_id>/', views.approve_response, name='approve_response'),
    path('response/reject/<int:response_id>/', views.reject_response, name='reject_response'),
    path('response/resend/<int:response_id>/', views.resend_response, name='resend_response'),
    path('process-existing-emails/', views.process_existing_emails, name='process_existing_emails'),
    path('debug/ai-status/', views.debug_ai_status, name='debug_ai_status'),
]