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

class IsFriendQuery(APIView):
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

class FriendsQuery(APIView):
    """
    Handles getting an authors friends and checking if anyone in a list is their friend.
    """

    def get(self, request, authorid, format=None):
        """
        Return a list of the authors friends.
        GET http://service/friends/<authorid>
        """
        try:
            author = Author.objects.get(uuid=authorid)
            friend_uuids = author.get_all_friend_uuids()
            return Response({"query": "friends", "authors": friend_uuids})
        except Author.DoesNotExist:
            return Response({'Error': 'The author does not exist.'}, status=status.HTTP_404_NOT_FOUND)


    def post(self, request, authorid, format=None):
        """
        Check if anyone in the authors list is the authors friend.
        Return a a list of authors from the original list who are in the friends list.
        POST to http://service/friends/<authorid>
        """
        # Validate the request data
        serializer = FriendsQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'Errors': serializer.errors}, status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data

        # Check that the author in the json data matches the author in the url
        if (authorid != data.get('author')):
            return Response({"Error": "The author uuid in the data does not match the author uuid in the url."}, status.HTTP_400_BAD_REQUEST)

        # Check that the author exists
        try:
            author = Author.objects.get(uuid=authorid)
        except Author.DoesNotExist:
            return Response({"Error": "The author does not exist."}, status.HTTP_404_NOT_FOUND)

        #  Check if anyone is the author's friend
        friend_uuids = author.get_all_friend_uuids()
        matching_uuids = []
        for friend_id in data.get('authors'):
            # Convert string to uuid
            if uuid.UUID(friend_id) in friend_uuids:
                matching_uuids.append(friend_id)

        return Response({"query": "friends", "author": authorid, "authors": matching_uuids})
