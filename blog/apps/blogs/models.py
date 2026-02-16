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

# Project modules
from apps.users.models import CustomUser

class Category(Model):
    NAME_MAX_LENGTH = 100

    name = CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Category name'
    )

    slug = SlugField(
        unique=True,
        verbose_name='Readable url'
    )

class Tag(Model):
    NAME_MAX_LENGTH = 50


    name = CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Category name'
    )

    slug = SlugField(
        unique=True,
        verbose_name='Readable url'
    )

class Status(TextChoices):
    DRAFT = 'draft', "Draft"
    PUBLISHED = 'published', 'Published'


class Post(Model):
    TITLE_MAX_LENGTH = 200

    author = ForeignKey(
        to=CustomUser,
        on_delete=CASCADE,
        verbose_name='Post author'
    )

    title = CharField(
        max_length=TITLE_MAX_LENGTH,
        verbose_name='Title'
    )

    slug = SlugField(
        unique=True,
        verbose_name='Readable url'
    )

    body = TextField(
        verbose_name='Post body'
    )

    category = ForeignKey(
        to=Category,
        on_delete=SET_NULL,
        null=True,
        verbose_name='Category'
    )

    tags = ManyToManyField(
        to=Tag,
        blank=True,
        verbose_name='Tags'
    )

    status = CharField(
        default = Status.DRAFT,
        choices = Status.choices,
        verbose_name='Post status'
    )

    created_at = DateTimeField(
        auto_now_add=True,
        verbose_name='Created date'
    )

    update_at = DateTimeField(
        auto_now=True,
        verbose_name='Updated date'
    )

class Comment(Model):
    post = ForeignKey(
        to=Post,
        on_delete=CASCADE,
        related_name='comments'
    )

    author = ForeignKey(
        to=CustomUser,
        on_delete=CASCADE
    )

    body = TextField()
    
    created_at = DateTimeField(
        auto_now_add=True
    )





