# Python modules
from typing import Any, Optional
import uuid
import logging


# Django modules
from rest_framework.viewsets import ViewSet
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, HTTP_204_NO_CONTENT
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils.text import slugify
from django.core.cache import cache


# Project modules
from apps.blogs.serializers import(
    PostCreateSerializer,
    PostListSerializer,
    PostUpdateSerializer,
    CommentListSerializer,
    CommentCreateSerializer
)
from apps.blogs.models import Post, Category, Tag, Comment
from apps.users.models import CustomUser
from apps.blogs.decorator import validate_serializer_data, rate_limit


class PostViewSet(ViewSet):
    """ViewSet for Post model"""
    lookup_field = 'slug'

    
    permission_classes = (AllowAny,)

    def get_permissions(self):
        if (self.action == 'create') or (self.action == 'partial_update') or (self.action == 'destroy') or ((self.action == 'create_comment' and self.request.method == 'POST')):
            return [IsAuthenticated()]
        return [AllowAny()]

    @validate_serializer_data(serializer_class=PostCreateSerializer)
    def create(
        self,
        request : DRFRequest,
        *args : tuple[Any, ...],
        **kwargs : dict[str, Any]
    ) -> DRFResponse:
        
        """Creating post method"""
        
        

        serializer : PostCreateSerializer = kwargs['serializer']

        data = serializer.validated_data

        def generate_unique_slug(title):
            base_slug = slugify(title)
            slug = base_slug
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
            return slug

        

        # creating Post object
        post : Post = Post.objects.create(
            author = data['author'],
            title = data['title'],
            category = data['category'],
            body = data['body'],
            slug = generate_unique_slug(data['title']),
            status = data.get('status', 'draft')
            
        ) 

        post.tags.set(data['tags'])

        cache.delete('published_posts')

        return DRFResponse(
            data=PostListSerializer(post, context={'request': request}).data,
            status=HTTP_201_CREATED
        )
    @rate_limit("list_posts", limit=20, timeout=60)
    def list(
        self,
        request : DRFRequest,
        *args : tuple[Any, ...],
        **kwargs : dict[str, Any]
    ) -> DRFResponse:
        """Get all post's"""
        cached_posts = cache.get("published_posts")

        if cached_posts:
            return DRFResponse(cached_posts)
        
        posts = Post.objects.filter(status = 'published')
        serializer = PostListSerializer(posts, many = True, context = {'request' : request})
        cache.set("published_posts", serializer.data, timeout=60)
        return DRFResponse(
            serializer.data
        )


    
    def retrieve(self, request, slug : str =None, *args, **kwargs):
        """Retrieve post by his slug"""
        try:
            post = Post.objects.get(slug=slug, status='published')
        except Post.DoesNotExist:
            return DRFResponse({"detail": "Post not found"}, status=HTTP_400_BAD_REQUEST)

        serializer = PostListSerializer(post, context={'request': request})
        return DRFResponse(serializer.data)
    
    def partial_update(
        self,
        request : DRFRequest,
        slug : str = None,
        *args : tuple[Any, ...],
        **kwargs : dict[str, Any]
        ) -> DRFResponse :
        """Patch method for Post model"""

        try:
            post = Post.objects.get(slug=slug)
        except Post.DoesNotExist:
            return DRFResponse({"detail": "Post not found"}, status=HTTP_400_BAD_REQUEST)
        

        if post.author != request.user:
            return DRFResponse({"detail": "You cannot edit this post"}, status=HTTP_403_FORBIDDEN)
        
        serializer : PostUpdateSerializer = PostUpdateSerializer(
            post,
            data = request.data,
            partial = True,
            context = {'request' : request}
        )
        cache.delete('published_posts')
        if serializer.is_valid():
            serializer.save()
            return DRFResponse(serializer.data, status=HTTP_200_OK)
        else:
            return DRFResponse(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def destroy(
        self,
        request : DRFRequest,
        slug : str = None,
        *args : tuple[Any, ...],
        **kwargs : dict[str, Any]
    ) -> DRFResponse:
        """Drop method for Post model"""
        
        try:
            post = Post.objects.get(slug=slug)
        except Post.DoesNotExist:
            return DRFResponse({"detail": "Post not found"}, status=HTTP_400_BAD_REQUEST)
        
        if post.author != request.user:
            return DRFResponse({"detail": "You can handle only your post's"}, status=HTTP_403_FORBIDDEN)
        

        post.delete()
        cache.delete('published_posts')

        return DRFResponse(status=HTTP_204_NO_CONTENT)
    
    @action(
        methods = ('POST',),
        detail = True,
        url_name = 'create_comment',
        url_path = 'comments',
        permission_classes = (IsAuthenticated,)
    )
    @validate_serializer_data(serializer_class=CommentCreateSerializer)
    def create_comment(
        self,
        request : DRFRequest,
        slug : str = None,
        *args : tuple[Any, ...],
        **kwargs : dict[str, Any]
    ) -> DRFResponse:
        """Creating comment for post"""

        try:
            post = Post.objects.get(slug=slug, status='published')
        except Post.DoesNotExist:
            return DRFResponse({"detail": "Post not found"}, status=HTTP_400_BAD_REQUEST)

        serializer : CommentCreateSerializer = kwargs['serializer']
        data = serializer.validated_data

        comment : Comment = Comment.objects.create(
            post = post,
            author = request.user,
            body = data['body']
        )

        return DRFResponse(
            data=CommentListSerializer(comment).data,
            status=HTTP_201_CREATED
        )
    @action(
        methods = ('GET',),
        detail = True,
        url_name = 'list_comments',
        url_path = 'list_comments',
        permission_classes = (AllowAny,)
    )
    def list_comments(
        self,
        request : DRFRequest,
        slug : str = None,
        *args : tuple[Any, ...],
        **kwargs : dict[str, Any]
    ) -> DRFResponse:
        """Get all comments for post"""

        try:
            post = Post.objects.get(slug=slug, status='published')
        except Post.DoesNotExist:
            return DRFResponse({"detail": "Post not found"}, status=HTTP_400_BAD_REQUEST)

        comments = post.comments.all()
        serializer = CommentListSerializer(comments, many=True)

        return DRFResponse(serializer.data)
    
    

    