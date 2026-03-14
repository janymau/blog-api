# Django modules
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone, translation
from django.utils.translation import gettext_lazy as _

# Project modules
from apps.users.models import CustomUser


def send_welcome_user_email(user: CustomUser) -> None:
    """
    Send a welcome email to a newly registered user in their preferred language.
    
    Args:
        user: CustomUser instance
        
    Raises:
        Exception: If email fails to send
    """
    language = user.preferred_language
    timezone_name = user.timezone or 'UTC'
    
    with translation.override(language):
        
        subject = render_to_string(
            "welcome_user_subject_template.txt",
            {"user": user}
        ).strip()
        
        context = {
            "user": user,
            "timezone": timezone_name,
        }
        
        body = render_to_string(
            "welcome_new_user_template.txt",
            context
        )
        
        try:
            email_message = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            
            email_message.encoding = 'utf-8'
            
            email_message.send(fail_silently=False)
            
        except Exception as e:
            print(f"Failed to send welcome email to {user.email}: {str(e)}")
            raise
