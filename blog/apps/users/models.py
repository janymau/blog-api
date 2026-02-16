# Python modules
from typing import Any

# Django modules
from django.db.models import CharField, EmailField, BooleanField, ImageField, DateTimeField
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

# Project modules
from apps.users.validators import check_domain_name

class CustomUserManager(BaseUserManager):
    """Custom user manager"""
    def _obtain_user_instance(
            self,
            email : str,
            first_name : str,
            last_name : str,
            password : str,
            **kwargs : dict[str, Any]

    ) -> 'CustomUser' : 
        """Get user instance"""
        if not email:
            raise ValidationError(
                message="Email field is required", code='email_empty'
            )
        if not first_name:
            raise ValidationError(
                message="First name field is required", code='first_name_empty'
            )
        if not last_name:
            raise ValidationError(
                message="Last name field is required", code='last_name_empty'
            )
        
        new_user : 'CustomUser' = self.model(
            email = self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            password = password,
            **kwargs
        )

        return new_user
    
    def create_user(
            self,
            email : str,
            first_name : str,
            last_name : str,
            password : str,
            **kwargs : dict[str, Any]
    ) -> 'CustomUser' :
        """Create a custom user"""
        new_user : 'CustomUser' = self._obtain_user_instance(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            **kwargs
        )

        new_user.set_password(password)
        new_user.save(using=self._db)

        return new_user
    
    def create_superuser(
            self,
            email : str,
            first_name : str,
            last_name : str,
            password : str,
            **kwargs : dict[str, Any]
    ) -> 'CustomUser' :
        """Create a custom superuser"""
        new_user : 'CustomUser' = self._obtain_user_instance(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            is_staff = True,
            is_superuser=True,
            **kwargs
        )

        new_user.set_password(password)
        new_user.save(using=self._db)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Custom user over a existing user model"""

    EMAIL_MAX_LENGTH = 100
    FIRST_NAME_MAX_LENGTH = 50
    LAST_NAME_MAX_LENGTH = 50
    PASSWORD_MAX_LENGTH = 254


    email = EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        db_index=True,
        validators=[check_domain_name],
        verbose_name='Email address',
        help_text='User email address / Unique nickname'
    )

    first_name = CharField(
        max_length=FIRST_NAME_MAX_LENGTH,
        verbose_name='User first name'
        
    )

    last_name = CharField(
        max_length=LAST_NAME_MAX_LENGTH,
        verbose_name='User last name'
    )

    password = CharField(
        max_length=PASSWORD_MAX_LENGTH,
        validators=[validate_password],
        verbose_name='Password',
        help_text='Hashed user password'
    )

    # True if the user can make the requests to the backend
    is_active = BooleanField(
        default=True,
        verbose_name='Active status',
        help_text= 'True if the user is active and has an access to request the data'   
    )

    # True if the user has admin rights
    is_staff = BooleanField(
        default=False,
        verbose_name='Staff status',
        help_text='True if user is part of company'
    )

    date_joined = DateTimeField(
        auto_now_add=True,
        verbose_name='User joined date'
    )

    avatar = ImageField(
        blank=True,
        null=True,
        verbose_name='User avatar'
    )



    REQUIRED_FIELDS = ["last_name", "first_name"]
    USERNAME_FIELD = 'email'
    objects = CustomUserManager()

    class Meta:
        """Meta options for CustomUser"""
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'
        ordering = ["-date_joined"]



        
        
