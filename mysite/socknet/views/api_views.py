from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response

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

class DoubleFriendQuery(APIView):
    """
    Ask if 2 authors are friends.
    GET http://service/friends/<authorid1>/<authorid2>
    where authorid1 and authorid2 are uuids
    """
    def get(self, request, authorid1, authorid2, format=None):
        author1 = None
        author2 = None
        is_friends = False
        #  At least one of the uuids must match an author in our system.
        try:
            author1 = Author.objects.get(uuid=authorid1)
        except Author.DoesNotExist:
            pass
        if author1:
            # Author1 is a local author, check if they are friends with author2.
            is_friends = author1.is_friend(authorid2)
        else:
            # Author1 is not a local author so we need to check if author2 is.
            try:
                author2 = Author.objects.get(uuid=authorid2)
            except Author.DoesNotExist:
                pass
            if author2:
                # Author2 is a local author, check if they are friends with author1.
                is_friends = author2.is_friend(authorid1)
            else:
                # Neither author is ours, return a 404.
                return Response({'Error': 'Neither author exists on this server.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({"query": "friends", "authors": [authorid1, authorid2], "friends": is_friends})
