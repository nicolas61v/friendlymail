from django.db import models
from django.contrib.auth.models import User


class GmailAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    token_expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.email} - {self.user.username}"


class Email(models.Model):
    gmail_account = models.ForeignKey(GmailAccount, on_delete=models.CASCADE, related_name='emails')
    gmail_id = models.CharField(max_length=255, unique=True)
    thread_id = models.CharField(max_length=255)
    subject = models.CharField(max_length=500, blank=True)
    sender = models.CharField(max_length=255)
    recipient = models.CharField(max_length=255)
    body_plain = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    received_date = models.DateTimeField()
    is_read = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-received_date']

    def __str__(self):
        return f"{self.subject[:50]} - {self.sender}"