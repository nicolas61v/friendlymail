from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from .gmail_service import GmailService
from .models import Email, GmailAccount


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'gmail_app/home.html')


def simple_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', 'testuser')
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password('testpass123')
            user.save()
        login(request, user)
        return redirect('dashboard')
    return render(request, 'gmail_app/login.html')


@login_required
def dashboard(request):
    try:
        gmail_account = GmailAccount.objects.get(user=request.user)
        emails = Email.objects.filter(gmail_account=gmail_account)[:20]
        context = {
            'gmail_account': gmail_account,
            'emails': emails,
            'has_gmail': True
        }
    except GmailAccount.DoesNotExist:
        context = {
            'has_gmail': False
        }
    
    return render(request, 'gmail_app/dashboard.html', context)


@login_required
def connect_gmail(request):
    gmail_service = GmailService(request.user)
    authorization_url = gmail_service.get_authorization_url(request)
    return redirect(authorization_url)


@login_required
def gmail_callback(request):
    try:
        gmail_service = GmailService(request.user)
        gmail_account = gmail_service.handle_oauth_callback(request)
        messages.success(request, f'Gmail account {gmail_account.email} connected successfully!')
        return redirect('sync_emails')
    except Exception as e:
        messages.error(request, f'Error connecting to Gmail: {str(e)}')
        return redirect('dashboard')


@login_required
def sync_emails(request):
    try:
        gmail_service = GmailService(request.user)
        synced_emails = gmail_service.sync_emails()
        messages.success(request, f'Synced {len(synced_emails)} new emails!')
    except Exception as e:
        messages.error(request, f'Error syncing emails: {str(e)}')
    
    return redirect('dashboard')


@login_required
def email_detail(request, email_id):
    try:
        email = Email.objects.get(id=email_id, gmail_account__user=request.user)
        return render(request, 'gmail_app/email_detail.html', {'email': email})
    except Email.DoesNotExist:
        messages.error(request, 'Email not found')
        return redirect('dashboard')