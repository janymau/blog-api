# Python modules
from typing import Any
import uuid
import logging

# Django modules
from rest_framework.viewsets import ViewSet
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.utils.text import slugify
from django.core.cache import cache
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiParameter,
    OpenApiExample, OpenApiResponse
)
from drf_spectacular.types import OpenApiTypes
from rest_framework.status import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN, HTTP_429_TOO_MANY_REQUESTS
)
from django.db.models import Count
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# Project modules
from apps.blogs.serializers import (
    PostCreateSerializer,
    PostListSerializer,
    PostUpdateSerializer,
    CommentListSerializer,
    CommentCreateSerializer
)
from apps.blogs.models import Post, Category, Tag, Comment
from apps.users.models import CustomUser
from apps.blogs.decorator import validate_serializer_data, rate_limit
from apps.notifications.tasks import process_new_comment


SUPPORTED_LANGUAGES = ['en', 'ru', 'kz'] 


def _post_cache_key(lang: str) -> str:
    return f'published_posts_{lang}'


def _invalidate_posts_cache() -> None:
    for lang in SUPPORTED_LANGUAGES:
        cache.delete(_post_cache_key(lang))


ERROR_400 = OpenApiResponse(
    description='Validation error',
    examples=[
        OpenApiExample(
            'Validation error',
            value={'detail': 'Post not found'},
            response_only=True,
            status_codes=[str(HTTP_400_BAD_REQUEST)]
        )
    ]
)

ERROR_401 = OpenApiResponse(
    description='Authentication credentials were not provided',
    examples=[
        OpenApiExample(
            'Unauthorized',
            value={'detail': 'Authentication credentials were not provided.'},
            response_only=True,
            status_codes=[str(HTTP_401_UNAUTHORIZED)]
        )
    ]
)

ERROR_403 = OpenApiResponse(
    description='Permission denied',
    examples=[
        OpenApiExample(
            'Forbidden',
            value={'detail': 'You cannot edit this post'},
            response_only=True,
            status_codes=[str(HTTP_403_FORBIDDEN)]
        )
    ]
)

ERROR_429 = OpenApiResponse(
    description='Rate limit exceeded',
    examples=[
        OpenApiExample(
            'Too many requests',
            value={'detail': 'Too many requests. Try again later.'},
            response_only=True,
            status_codes=[str(HTTP_429_TOO_MANY_REQUESTS)]
        )
    ]
)


# --- PostViewSet ---

@extend_schema_view(
    list=extend_schema(
        summary='List published posts',
        description=(
            'Returns all published posts. '
            'Dates are formatted in the user timezone and active locale. '
            'Results are cached per language in Redis.'
        ),
        tags=['Posts'],
        parameters=[
            OpenApiParameter(
                name='lang',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Override active language (en, ru, kz)',
                required=False,
                enum=['en', 'ru', 'kz']
            )
        ],
        responses={
            HTTP_200_OK: PostListSerializer(many=True),
            HTTP_429_TOO_MANY_REQUESTS: ERROR_429,
        },
        examples=[
            OpenApiExample(
                'Success response',
                value=[{
                    'id': 1,
                    'title': 'My first post',
                    'author': {'id': 1, 'email': 'user@example.com'},
                    'slug': 'my-first-post',
                    'category': {'id': 1, 'name': 'Technology', 'slug': 'technology'},
                    'body': 'Post content here',
                    'tags': [{'id': 1, 'name': 'django', 'slug': 'django'}],
                    'comment_count': 3,
                    'status': 'published',
                    'created_at': 'March 14, 2026, 9:00 a.m.'
                }],
                response_only=True,
                status_codes=[str(HTTP_200_OK)]
            )
        ]
    ),
    create=extend_schema(
        summary='Create a post',
        description=(
            'Creates a new post. '
            'Category can be passed as an integer ID or a string name — '
            'if the name does not exist it will be created automatically. '
            'Tags are created automatically if they do not exist. '
            'Requires JWT authentication.'
        ),
        tags=['Posts'],
        responses={
            HTTP_201_CREATED: PostListSerializer,
            HTTP_400_BAD_REQUEST: ERROR_400,
            HTTP_401_UNAUTHORIZED: ERROR_401,
            HTTP_429_TOO_MANY_REQUESTS: ERROR_429,
        },
        examples=[
            OpenApiExample(
                'Request body',
                value={
                    'author': 1,
                    'title': 'My post',
                    'category': 'Technology',
                    'tags': ['django', 'python'],
                    'body': 'Post content',
                    'status': 'published'
                },
                request_only=True,
            ),
            OpenApiExample(
                'Created response',
                value={
                    'id': 5,
                    'title': 'My post',
                    'author': {'id': 1, 'email': 'user@example.com'},
                    'slug': 'my-post-3f9a1c',
                    'category': {'id': 1, 'name': 'Technology', 'slug': 'technology'},
                    'body': 'Post content',
                    'tags': [{'id': 1, 'name': 'django', 'slug': 'django'}],
                    'comment_count': 0,
                    'status': 'published',
                    'created_at': 'March 14, 2026, 9:00 a.m.'
                },
                response_only=True,
                status_codes=[str(HTTP_201_CREATED)]
            ),
            OpenApiExample(
                'Validation error',
                value={'title': ['This field is required.']},
                response_only=True,
                status_codes=[str(HTTP_400_BAD_REQUEST)]
            )
        ]
    ),
    retrieve=extend_schema(
        summary='Retrieve a post',
        description='Returns a single published post by its slug.',
        tags=['Posts'],
        responses={
            HTTP_200_OK: PostListSerializer,
            HTTP_400_BAD_REQUEST: ERROR_400,
        },
        examples=[
            OpenApiExample(
                'Post not found',
                value={'detail': 'Post not found'},
                response_only=True,
                status_codes=[str(HTTP_400_BAD_REQUEST)]
            )
        ]
    ),
    partial_update=extend_schema(
        summary='Partially update a post',
        description=(
            'Updates one or more fields on a post. '
            'Only the original author can edit their own post. '
            'Requires JWT authentication.'
        ),
        tags=['Posts'],
        responses={
            HTTP_200_OK: PostUpdateSerializer,
            HTTP_400_BAD_REQUEST: ERROR_400,
            HTTP_401_UNAUTHORIZED: ERROR_401,
            HTTP_403_FORBIDDEN: ERROR_403,
        },
        examples=[
            OpenApiExample(
                'Request body',
                value={'title': 'Updated title', 'status': 'published'},
                request_only=True,
            ),
            OpenApiExample(
                'Forbidden',
                value={'detail': 'You cannot edit this post'},
                response_only=True,
                status_codes=[str(HTTP_403_FORBIDDEN)]
            )
        ]
    ),
    destroy=extend_schema(
        summary='Delete a post',
        description=(
            'Permanently deletes a post. '
            'Only the original author can delete their own post. '
            'Requires JWT authentication.'
        ),
        tags=['Posts'],
        responses={
            HTTP_204_NO_CONTENT: OpenApiResponse(description='Deleted successfully'),
            HTTP_400_BAD_REQUEST: ERROR_400,
            HTTP_401_UNAUTHORIZED: ERROR_401,
            HTTP_403_FORBIDDEN: ERROR_403,
        },
    ),
)
class PostViewSet(ViewSet):
    """ViewSet for Post model"""
    lookup_field = 'slug'
    permission_classes = (AllowAny,)

    def get_permissions(self):
        if self.action in ('create', 'partial_update', 'destroy') or (
            self.action == 'create_comment' and self.request.method == 'POST'
        ):
            return [IsAuthenticated()]
        return [AllowAny()]

    @validate_serializer_data(serializer_class=PostCreateSerializer)
    def create(self, request: DRFRequest, *args, **kwargs) -> DRFResponse:
        """Create a post"""
        serializer: PostCreateSerializer = kwargs['serializer']
        data = serializer.validated_data

        def generate_unique_slug(title):
            base_slug = slugify(title)
            slug = base_slug
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
            return slug

        post: Post = Post.objects.create(
            author=data['author'],
            title=data['title'],
            category=data['category'],
            body=data['body'],
            slug=generate_unique_slug(data['title']),
            status=data.get('status', 'draft')
        )
        post.tags.set(data['tags'])
        _invalidate_posts_cache()

        return DRFResponse(
            data=PostListSerializer(post, context={'request': request}).data,
            status=HTTP_201_CREATED
        )

    @rate_limit("list_posts", limit=20, timeout=60)
    def list(self, request: DRFRequest, *args, **kwargs) -> DRFResponse:
        """List all published posts"""
        lang = get_language() or 'en'
        cache_key = _post_cache_key(lang)

        cached = cache.get(cache_key)
        if cached is not None:
            return DRFResponse(cached)

        posts = Post.objects.filter(status='published')
        serializer = PostListSerializer(posts, many=True, context={'request': request})
        cache.set(cache_key, serializer.data, timeout=60)
        return DRFResponse(serializer.data)

    def retrieve(self, request: DRFRequest, slug: str = None, *args, **kwargs) -> DRFResponse:
        """Retrieve a post by slug"""
        post = Post.objects.filter(slug=slug, status='published') \
    .annotate(comment_count=Count('comments')) \
    .first()
        if not post:
            return DRFResponse({"detail": _("Post not found")}, status=HTTP_400_BAD_REQUEST)

        return DRFResponse(PostListSerializer(post, context={'request': request}).data)

    def partial_update(self, request: DRFRequest, slug: str = None, *args, **kwargs) -> DRFResponse:
        """Partially update a post"""
        try:
            post = Post.objects.get(slug=slug)
        except Post.DoesNotExist:
            return DRFResponse({"detail": _("Post not found")}, status=HTTP_400_BAD_REQUEST)

        if post.author != request.user:
            return DRFResponse({"detail": _("You cannot edit this post")}, status=HTTP_403_FORBIDDEN)

        serializer = PostUpdateSerializer(post, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            _invalidate_posts_cache()
            return DRFResponse(serializer.data, status=HTTP_200_OK)
        return DRFResponse(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def destroy(self, request: DRFRequest, slug: str = None, *args, **kwargs) -> DRFResponse:
        """Delete a post"""
        try:
            post = Post.objects.get(slug=slug)
        except Post.DoesNotExist:
            return DRFResponse({"detail": _("Post not found")}, status=HTTP_400_BAD_REQUEST)

        if post.author != request.user:
            return DRFResponse({"detail": _("You can handle only your posts")}, status=HTTP_403_FORBIDDEN)

        post.delete()
        _invalidate_posts_cache()
        return DRFResponse(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        summary='Create a comment',
        description='Adds a comment to a published post. Requires JWT authentication.',
        tags=['Comments'],
        responses={
            HTTP_201_CREATED: CommentListSerializer,
            HTTP_400_BAD_REQUEST: ERROR_400,
            HTTP_401_UNAUTHORIZED: ERROR_401,
        },
        examples=[
            OpenApiExample(
                'Request body',
                value={'body': 'Great post!'},
                request_only=True,
            ),
            OpenApiExample(
                'Created response',
                value={'id': 1, 'author': 1, 'post': 3, 'body': 'Great post!'},
                response_only=True,
                status_codes=[str(HTTP_201_CREATED)]
            )
        ]
    )
    @action(methods=('POST',), detail=True, url_name='create_comment', url_path='comments', permission_classes=(IsAuthenticated,))
    @validate_serializer_data(serializer_class=CommentCreateSerializer)
    def create_comment(self, request: DRFRequest, slug: str = None, *args, **kwargs) -> DRFResponse:
        """Create a comment on a post"""
        try:
            post = Post.objects.get(slug=slug, status='published')
        except Post.DoesNotExist:
            return DRFResponse({"detail": _("Post not found")}, status=HTTP_400_BAD_REQUEST)

        serializer: CommentCreateSerializer = kwargs['serializer']
        comment = Comment.objects.create(
            post=post,
            author=request.user,
            body=serializer.validated_data['body']
        )

        process_new_comment.delay(comment.id)
        

        return DRFResponse(CommentListSerializer(comment).data, status=HTTP_201_CREATED)
    

    @extend_schema(
        summary='List comments for a post',
        description='Returns all comments for a given published post.',
        tags=['Comments'],
        responses={
            HTTP_200_OK: CommentListSerializer(many=True),
            HTTP_400_BAD_REQUEST: ERROR_400,
        },
        examples=[
            OpenApiExample(
                'Success response',
                value=[{'id': 1, 'author': 1, 'post': 3, 'body': 'Great post!'}],
                response_only=True,
                status_codes=[str(HTTP_200_OK)]
            )
        ]
    )
    @action(methods=('GET',), detail=True, url_name='list_comments', url_path='list_comments', permission_classes=(AllowAny,))
    def list_comments(self, request: DRFRequest, slug: str = None, *args, **kwargs) -> DRFResponse:
        """List all comments for a post"""
        try:
            post = Post.objects.get(slug=slug, status='published')
        except Post.DoesNotExist:
            return DRFResponse({"detail": _("Post not found")}, status=HTTP_400_BAD_REQUEST)

        return DRFResponse(CommentListSerializer(post.comments.all(), many=True).data)

