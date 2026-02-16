# Django modules
from django.core.exceptions import ValidationError

PROHIBITED_EMAILS = [

]

def check_domain_name(value : str) -> None:
    """Validate email domain name"""
    domain : str = value.split('@')[1]

    if domain in PROHIBITED_EMAILS:
        raise ValidationError(
            message= f"Registration using \ {domain} \ is not allowed",
            code = 'invalid_email_domain'
        )
    