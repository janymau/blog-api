# Python modules
from typing import Any, Optional
import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Django modules
from rest_framework.serializers import (
    Serializer, ModelSerializer, CharField, EmailField,
    IntegerField, ListField, ChoiceField, ValidationError as DRFValidationError
)
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

# Project modules
from apps.users.models import CustomUser

logger = logging.getLogger("users")

SUPPORTED_LANGUAGES = [
    ("en", "English"),
    ("ru", "Russian"),
    ("kz", "Kazakh"),
]


def validate_timezone_value(value: str) -> str:
    """Validate IANA timezone. Returns value on success, raises on failure."""
    try:
        ZoneInfo(value)
        return value
    except (ZoneInfoNotFoundError, KeyError):
        raise DRFValidationError(
            _("Invalid timezone. Use a valid IANA timezone name, for example: Asia/Almaty.")
        )


class UserLoginResponseSerializer(Serializer):
    """Serializer for user login response"""
    id = IntegerField()
    first_name = CharField()
    last_name = CharField()
    email = EmailField()
    access = CharField()
    refresh = CharField()

    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'access', 'refresh')


class UserLoginFailSerializer(Serializer):
    """Serializer for user login error"""
    email = ListField(child=CharField(), required=False)
    password = ListField(child=CharField(), required=False)

    class Meta:
        fields = ('email', 'password')


class HTTP405MethodNowAllowedSerializer(Serializer):
    """Serializer for 405 HTTP method"""
    detail = CharField()

    class Meta:
        fields = ('detail',)


class UserLoginSerializer(Serializer):
    """Serializer for user login"""
    email = EmailField(required=True, max_length=CustomUser.EMAIL_MAX_LENGTH)
    password = CharField(required=True, max_length=CustomUser.PASSWORD_MAX_LENGTH)

    class Meta:
        fields = ('email', 'password')

    def validate_email(self, value: str) -> str:
        return value.lower()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validates input data"""
        email: str = attrs['email']
        password: str = attrs['password']

        user: Optional[CustomUser] = CustomUser.objects.filter(email=email).first()

        if not user:
            logger.warning(f"Login attempt with non-existent email: {email}")
            raise ValidationError(
                {"email": [gettext("User with this email %(email)s does not exist") % {"email": email}]}
            )

        if not user.check_password(raw_password=password):
            logger.warning("Login attempt with wrong password")
            raise ValidationError({"password": _("Incorrect password")})

        attrs['user'] = user
        return super().validate(attrs)
    

class UserRegisterResponseSerializer(Serializer):
    """Serializer for user register response"""
    id = IntegerField()
    first_name = CharField()
    last_name = CharField()
    email = EmailField()

    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email')


class UserRegisterFailSerializer(Serializer):
    """Serializer for user register error"""
    email = ListField(child=CharField(), required=False)
    password = ListField(child=CharField(), required=False)

    class Meta:
        fields = ('email', 'password')


class UserRegisterSerializer(Serializer):
    """Serializer for custom user registration"""

    first_name = CharField(required=True, max_length=CustomUser.FIRST_NAME_MAX_LENGTH)
    last_name = CharField(required=True, max_length=CustomUser.LAST_NAME_MAX_LENGTH)
    email = EmailField(required=True, max_length=CustomUser.EMAIL_MAX_LENGTH)
    password = CharField(required=True, max_length=CustomUser.PASSWORD_MAX_LENGTH)

    preferred_language = ChoiceField(
        choices=SUPPORTED_LANGUAGES,
        label=_("User preferred language"),
        required=False,
        default='en'
    )
    timezone = CharField(
        label=_("Timezone"),
        required=False,
        default='UTC'
    )

    class Meta:
        fields = ['first_name', 'last_name', 'email', 'password', 'preferred_language', 'timezone']

    def validate_preferred_language(self, value: str) -> str:
        return value.lower()

    def validate_timezone(self, value: str) -> str:
        return validate_timezone_value(value)

    def validate_email(self, value: str) -> str:
        value = value.lower()
        if CustomUser.objects.filter(email=value).exists():
            logger.warning(f"Registration attempt with existing email: {value}")
            raise ValidationError(
                message=[gettext("This email address %(value)s already exist") % {'value': value}]
            )
        return value

    def validate_password(self, value: str) -> str:
        try:
            validate_password(value)
        except ValidationError as e:
            raise ValidationError(list(e.messages))
        return value


class UserPreferredLanguage(Serializer):
    """Serializer for updating user's preferred language"""
    preferred_language = ChoiceField(
        choices=SUPPORTED_LANGUAGES,
        label=_("Preferred Language")
    )

    def validate_preferred_language(self, value: str) -> str:
        return value.lower()


class UserPrefferedTimezone(Serializer):
    """Serializer for updating user's preferred timezone"""
    timezone = CharField(label=_("Timezone"))

    def validate_timezone(self, value: str) -> str:
        return validate_timezone_value(value)


class UserForeignSerializer(ModelSerializer):
    """Serializer for User foreign representative"""

    class Meta:
        model = CustomUser
        fields = ("id", "email")