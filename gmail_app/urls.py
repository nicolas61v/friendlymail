from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.simple_login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('connect-gmail/', views.connect_gmail, name='connect_gmail'),
    path('gmail/callback/', views.gmail_callback, name='gmail_callback'),
    path('sync-emails/', views.sync_emails, name='sync_emails'),
    path('email/<int:email_id>/', views.email_detail, name='email_detail'),
]