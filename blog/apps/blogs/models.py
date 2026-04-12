# Python modules
from typing import Any

# Django modules
from django.db.models import (
    CharField,
    Model,
    SlugField,
    ForeignKey,
    TextField,
    ManyToManyField,
    DateTimeField,
    CASCADE,
    SET_NULL,
    TextChoices
)
from django.utils.translation import gettext_lazy as _, get_language

# Project modules
from apps.users.models import CustomUser

class Category(Model):
    NAME_MAX_LENGTH = 100
    
    name_en = CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True,
        verbose_name=_('Category name in English'),
        
    )

    name_ru = CharField(
        max_length=NAME_MAX_LENGTH,
        verbose_name=_('Category name in Russian'),
        
    )

    name_kz = CharField(
        max_length=NAME_MAX_LENGTH,
        verbose_name=_('Category name in Kazakh'),
        
    )

    slug = SlugField(
        unique=True,
        verbose_name=_('Readable url')
    )

    @property
    def localized_name(
        self,

    ) -> str :
        """Return Category model on user preferred language"""
        lang = (get_language() or 'en').split('-')[0].lower()
        return getattr(
            self,
            f"name_{lang}",
            None,

        ) or self.name_en
    
    def __str__(self):
        """Return Categoty model in readable string way"""
        return self.localized_name
    
    

class Tag(Model):
    NAME_MAX_LENGTH = 50


    name = CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True,
        verbose_name=_('Tag name')
    )

    slug = SlugField(
        unique=True,
        verbose_name=_('Readable url')
    )

class Status(TextChoices):
        DRAFT     = 'draft',     'Draft'
        PUBLISHED = 'published', 'Published'
        SCHEDULED = 'scheduled', 'Scheduled'


class Post(Model):
    TITLE_MAX_LENGTH = 200
    STATUS_MAX_LENGTH = 20


    author = ForeignKey(
        to=CustomUser,
        on_delete=CASCADE,
        verbose_name=_('Post author')
    )

    title = CharField(
        max_length=TITLE_MAX_LENGTH,
        verbose_name=_('Title')
    )

    slug = SlugField(
        unique=True,
        verbose_name=_('Readable url')
    )

    body = TextField(
        verbose_name=_('Post body')
    )

    category = ForeignKey(
        to=Category,
        on_delete=SET_NULL,
        null=True,
        verbose_name=_('Category')
    )

    tags = ManyToManyField(
        to=Tag,
        blank=True,
        verbose_name=_('Tags')
    )

    status = CharField(
        max_length = STATUS_MAX_LENGTH,
        default = Status.DRAFT,
        choices = Status.choices,
        verbose_name=_('Post status')
    )

    created_at = DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created date')
    )

    update_at = DateTimeField(
        auto_now=True,
        verbose_name=_('Updated date')
    )
    
    publish_at = DateTimeField(null=True, blank=True) 

class Comment(Model):
    post = ForeignKey(
        to=Post,
        on_delete=CASCADE,
        related_name=_('comments')
    )

    author = ForeignKey(
        to=CustomUser,
        on_delete=CASCADE
    )

    body = TextField()
    
    created_at = DateTimeField(
        auto_now_add=True
    )





