from rest_framework import viewsets

from socknet.serializers import *
from socknet.models import Author, Post

class AuthorPostsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that
    """
    queryset = Author.objects.all()
    serializer_class = AuthorPostsSerializer

class PostsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows posts to be viewed or edited.
    """
    queryset = Post.objects.all().order_by('-created_on')
    serializer_class = PostsSerializer

class AuthorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that
    """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
