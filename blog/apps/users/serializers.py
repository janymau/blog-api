# Python modules
from typing import Any, Optional
import logging


# Django modules
from rest_framework.serializers import Serializer, ModelSerializer ,CharField, EmailField, IntegerField, ListField
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password


# Project modules
from apps.users.models import CustomUser

logger = logging.getLogger("users")

class UserLoginResponseSerializer(Serializer):
    logger.debug(f"User request entered into UserLoginResponseSerializer serializer")
    """Serializer for user login response"""
    id = IntegerField()
    first_name = CharField()
    last_name = CharField()
    email = EmailField()
    access = CharField()
    refresh = CharField()

    class Meta:
        """Custom metadata"""
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'access',
            'refresh'
        )

class UserLoginFailSerializer(Serializer):
    logger.warning(f"User request entered into UserLoginFailSerializer")
    """Serializer for user login error"""

    email = ListField(
        child = CharField(),
        required = False
    )

    password = ListField(
        child = CharField(),
        required = False
    )


    class Meta:
        """Customization of metadata"""

        fields = (
            'email',
            'password'
        )

class HTTP405MethodNowAllowedSerializer(Serializer):
    """Serializer for 405 HTTP method"""

    detail = CharField()

    class Meta:
        """Customization of metadata"""

        fields = (
            'detail'
        )

class UserLoginSerializer(Serializer):
    logger.debug(f"User request entered into UserLoginSerializer serializer")

    """Serializer for user login"""

    email = EmailField(
        required = True,
        max_length = CustomUser.EMAIL_MAX_LENGTH
    )

    password = CharField(
        required = True,
        max_length = CustomUser.PASSWORD_MAX_LENGTH
    )

    class Meta:
        """Customization of metadata for User login Serializer"""

        fields = (
            'email',
            'password'
        )

    def validate_email(self, value: str) -> str:
            return value.lower()
        
    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
            """Validates input data"""

            email : str = attrs['email']
            password : str = attrs['password']

            user : Optional[CustomUser] = CustomUser.objects.filter(email = email).first()

            if not user:
                logger.warning(f"User request has problems with {email}, this email does not exist")
                raise ValidationError(
                    {
                        "email" : [f"User with this email {email} does not exist"]
                    }
                )

            if not user.check_password(raw_password=password):
                logger.warning(f"User request has problems with password, wrong password has entered")
                raise ValidationError(
                    {
                        "password" : f"Incorrect password"
                    }
                )
            

            attrs['user'] = user
            

            return super().validate(attrs)
        

class UserRegisterResponseSerializer(Serializer):
    """Serializer for user register response"""
    id = IntegerField()
    first_name = CharField()
    last_name = CharField()
    email = EmailField()

    class Meta:
        """Custom metadata"""
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
        )

class UserRegisterFailSerializer(Serializer):
    """Serializer for user register error"""

    email = ListField(
        child = CharField(),
        required = False
    )

    password = ListField(
        child = CharField(),
        required = False
    )


    class Meta:
        """Customization of metadata"""

        fields = (
            'email',
            'password'
        )

class UserRegisterSerializer(Serializer):
    """Serializer for custom user registration"""
    logger.debug(f"User request data entered the UserRegisterSerializer")

    first_name = CharField(
        required = True,
        max_length = CustomUser.FIRST_NAME_MAX_LENGTH
    )

    last_name = CharField(
        required = True,
        max_length = CustomUser.LAST_NAME_MAX_LENGTH
    )

    email = EmailField(
        required = True,
        max_length = CustomUser.EMAIL_MAX_LENGTH
    )

    password = CharField(
        required = True,
        max_length = CustomUser.PASSWORD_MAX_LENGTH
    )

    class Meta:
        """Customization of metadata"""
        fields = [
            'first_name',
            'last_name',
            'email',
            'password'
        ]

    def validate_email(self, value: str) -> str:
            value : str = value.lower()


            if CustomUser.objects.filter(email = value).exists():
                logger.warning(f"User request has problems with {value}, this email already exist")
                raise ValidationError(
                    
                    message= f"This email address {value} already exist"
                )
            return value
    
    def validate_password(self, value : str) -> str:
        logger.debug(f"User request data entered the validate_password function")
        try:
            validate_password(value)
            logger.debug(f"User request data validate_password success!")

        except ValidationError as e:
            logger.warning(f"User request data failed the validate_password function")
            raise ValidationError(list(e.messages))
        return value
    

class UserForeignSerializer(ModelSerializer):
     """Serializer for User foreign representative"""

     class Meta:
          
          
          """
          Customize the serializer's metadata.
          """
          model = CustomUser
          fields = (
            "id",
            "email",
        )