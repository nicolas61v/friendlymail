"""
Views package - Modular organization of views

This package organizes views into logical modules:
- auth_views: User authentication (register, login, logout)
- email_views: Email management (dashboard, sync, details)
- gmail_views: Gmail-specific functionality
- outlook_views: Outlook-specific functionality
- account_views: Generic account management
- ai_response_views: AI response management
- ai_role_views: AI role configuration
- system_views: System utilities and logs

All views are re-exported here for backward compatibility with existing URLconf.
"""

# Authentication views
from .auth_views import (
    home,
    user_register,
    user_login,
    user_logout,
)

# Email management views
from .email_views import (
    dashboard,
    email_detail,
    sync_emails,
    sync_emails_api,
    sync_all_accounts,
    get_all_emails_with_ai_status,
)

# Gmail-specific views
from .gmail_views import (
    connect_gmail,
    gmail_callback,
    disconnect_gmail,
    clear_oauth_session,
)

# Outlook-specific views
from .outlook_views import (
    connect_outlook,
    outlook_callback,
    sync_outlook,
    disconnect_outlook,
)

# Generic account views
from .account_views import (
    disconnect_email_account,
)

# AI Response views
from .ai_response_views import (
    ai_responses,
    approve_response,
    reject_response,
    resend_response,
    edit_response,
    process_existing_emails,
)

# AI Role views
from .ai_role_views import (
    ai_roles_list,
    ai_role_create,
    ai_role_edit,
    ai_role_activate,
    ai_role_delete,
    ai_role_temporal_rule_save,
    ai_role_temporal_rule_delete,
)

# System views
from .system_views import (
    system_logs,
)

__all__ = [
    # Auth
    'home',
    'user_register',
    'user_login',
    'user_logout',
    # Email
    'dashboard',
    'email_detail',
    'sync_emails',
    'sync_emails_api',
    'sync_all_accounts',
    'get_all_emails_with_ai_status',
    # Gmail
    'connect_gmail',
    'gmail_callback',
    'disconnect_gmail',
    'clear_oauth_session',
    # Outlook
    'connect_outlook',
    'outlook_callback',
    'sync_outlook',
    'disconnect_outlook',
    # Account
    'disconnect_email_account',
    # AI Responses
    'ai_responses',
    'approve_response',
    'reject_response',
    'resend_response',
    'edit_response',
    'process_existing_emails',
    # AI Roles
    'ai_roles_list',
    'ai_role_create',
    'ai_role_edit',
    'ai_role_activate',
    'ai_role_delete',
    'ai_role_temporal_rule_save',
    'ai_role_temporal_rule_delete',
    # System
    'system_logs',
]
