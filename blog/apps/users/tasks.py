"""
Retry policy rationale:
Email delivery depends on an external SMTP server which can be temporarily
unavailable (rate limits, network blips). Automatic retries with exponential
backoff prevent losing welcome emails without blocking the request thread.
"""

# Django modules
from django.core.mail import send_mail
from django.conf import settings

# Celery
from celery import shared_task

@shared_task(
    autoretry_for = (Exception, ),
    retry_backoff = True,
    max_retries = 3 
)
def send_welcome_email(user_email: str, username: str) -> None:
    send_mail(
        subject='Welcome to the blog!',
        message=f'Hi {username}, thanks for registering.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
    )




