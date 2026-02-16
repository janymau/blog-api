# Python modules
from typing import Any, Optional

# Django modules
from rest_framework.serializers import (
    Serializer,
    CharField,
    SlugField,
    ModelSerializer,
    SerializerMethodField,
    Field,
    PrimaryKeyRelatedField,
    ListField,
    SlugRelatedField
)
from django.core.exceptions import ValidationError
from django.utils.text import slugify

# Project modules
from apps.blogs.models import Category,Tag,Comment, Post
from apps.users.serializers import UserForeignSerializer


class CurrentSLUGDefault:
    """Default value for pk field in serializer"""

    requires_context = True

    def __call__(self, serializer_field: Field):
        """Get current slug from the request"""
        view = serializer_field.context.get('view')

        assert view is not None, (
            'CurrentSlugDefault requires slug in the serializer context'
        )

        slug = view.kwargs.get('slug')

        assert slug is not None, (
            'CurrentSlugDefault requires slug in the URL kwargs'
        )

        return slug
    



    def __repr__(self) -> str:
        """Return a string representation of the default."""
        return "%s()" % self.__class__.__name__



class PostBaseSerializer(ModelSerializer):
    """Base seriazlizer for Post instance"""
    
    class Meta:
        """Customize serializer metadata"""
        model = Post
        fields = "__all__"




class CategoryBaseSerializer(ModelSerializer):
    """
    Base serializer for Category Model
    """

    class Meta:
        model = Category
        fields = '__all__'
    

class CategoryListSerializer(CategoryBaseSerializer):
    """
    Serializer for Category list
    """

    class Meta:
        """Customization of metadata"""
        model = Category
        fields = ("id", 'name', "slug")

class CategoryField(Field):

    def to_internal_value(self, data):
        if isinstance(data, int):
            try:
                return Category.objects.get(pk=data)
            except Category.DoesNotExist:
                raise ValidationError({"category": f"Category with id {data} does not exist"})
        
        if isinstance(data, str):
            category, _ = Category.objects.get_or_create(
                name=data,
                defaults={'slug': slugify(data)}
            )
            return category

        raise ValidationError({"category": "Invalid category format"})

    def to_representation(self, value):
        return value.id
    

class TagBaseSerializer(ModelSerializer):
    """
    Docstring for TagBaseSerializer
    """

    class Meta:
        model = Tag
        fields = '__all__'

class TagListSerializer(ModelSerializer):
    """
    Serializer for Tag list
    """

    class Meta:
        """Customazitaion of metadata"""
        model = Tag
        fields = ("id", "name", "slug")

class TagListField(ListField):
    """Field for creating Tag object from name : str """
    child = CharField()

    def to_internal_value(self, data : list[str]):
        tag_names = set(data)

        existing_tags = Tag.objects.filter(name__in=tag_names)
        existing_names = set(existing_tags.values_list("name" , flat=True))

        new_names = tag_names - existing_names

        new_tags = [
            Tag(name = name, slug = slugify(name))
            for name in new_names
        ]

        Tag.objects.bulk_create(new_tags)
        all_tags = list(existing_tags) + new_tags

        print(all_tags)
        return all_tags
    
    def to_representation(self, value):
        return [tag.id for tag in value]


class CommentBaseSerializer(ModelSerializer):
    """
    Docstring for CommentBaseSerializer
    """

    class Meta:
        model = Comment
        fields = "__all__"


class CommentListSerializer(CommentBaseSerializer):
    """
    Docstring for CommentListSerializer
    """
    
    class Meta:
        model = Comment
        fields = (
            'id',
            'author',
            'post',
            'body'
        )

class CommentCreateSerializer(CommentBaseSerializer):
    """
    Docstring for CommentCreateSerializer
    
    :var author: Description
    :vartype author: ListSerializer | Any | UserForeignSerializer
    :var comment_count: Description
    :vartype comment_count: SerializerMethodField
    :var tags: Description
    :vartype tags: ListSerializer | Any | TagListSerializer
    """
    class Meta:
        model = Comment
        fields = ['body']

class PostCreateSerializer(PostBaseSerializer):
    """Serializer for post create request"""
    category = CategoryField()
    tags = TagListField(write_only = True)
    class Meta:
        """Customization of metadata"""
        model = Post
        fields = (
            'id',
            'author',
            'title',
            'category',
            'tags',
            'body',
            'status'
        )


class PostUpdateSerializer(PostBaseSerializer):
    """Serializer for Post model update"""
    category = CategoryField()
    
    tags = TagListField(write_only = True)

    tags_new = TagListSerializer(read_only = True, many = True, source = 'tags')

    class Meta:
        """Customization of metadata"""
        model = Post
        fields = ('title', 'category', 'tags', 'tags_new', 'body', 'status')

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.body = validated_data.get('body', instance.body)
        instance.status = validated_data.get('status', instance.status)

        if 'category' in validated_data:
            instance.category = validated_data['category']

        if 'tags' in validated_data:
            instance.tags.set(validated_data['tags'])
        

        instance.save()
        return instance

class PostListSerializer(PostBaseSerializer):
    """Serizalizer for listing post's"""

    author = UserForeignSerializer()

    comment_count = SerializerMethodField(
        method_name = "get_comment_count",
    )
    tags = TagListSerializer(many = True)

    class Meta:
        model = Post
        fields = (
            'id',
            'title',
            'author',
            'slug',
            'category',
            'body',
            'tags',
            'comment_count',
            'status'

        )
    
    def get_comment_count(self, obj : Post) -> int:
        return getattr(obj, "comment_count", 0)

class PostDeleteSerializer(PostBaseSerializer):
    """
    Serializer for Post model drop
    """
