import base64
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from socknet.serializers import *
from socknet.models import Author, Post, ImageServ, Comment
from socknet.utils import *

### HELPER FUNCTIONS ###

def get_page_size(request, paginator):
    if (request.GET.get('size')):
        return int(request.GET.get('size'))
    else:
        return paginator.page_size

### PAGINATION ###
class PostsPagination(PageNumberPagination):
    page_size = 50
    # Doesn't look like the spec requires us to allow page size specifying, just which page?
    page_size_query_param = 'size'
    # max_page_size = 10

class AuthorPostsPagination(PageNumberPagination):
    page_size = 50

### API VIEWS ###
class AuthorPostsViewSet(APIView):
    """
    API endpoint that allows an authenticated user to see all posts they are allowed to see
    GET /api/author/posts
    """
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = AuthorPostsPagination

    def get(self, request, format=None):
        content = {'user': unicode(request.user), 'auth': unicode(request.auth),}

        try:
            """
            SEND EVERYTHING BUT SERVERONLY BECAUSE HINDLE SAID ITS THE CLIENTS
            RESPONSIBILITY TO FILTER SHIT
            """
            final_queryset = Post.objects.exclude(visibility="SERVERONLY").order_by('-created_on')

            paginator = PostsPagination()
            posts = paginator.paginate_queryset(final_queryset, request)
            for post in posts:
                # TODO: Difference in source vs origin?
                post.source = request.scheme + "://" + str(request.META["HTTP_HOST"]) + "/posts/" + str(post.id)
                post.origin = request.scheme + "://" + str(request.META["HTTP_HOST"]) + "/posts/" + str(post.id)
                post.published = post.created_on
                if (post.markdown == False):
                    post.contentType = "text/plain"
                else:
                    post.contentType = "text/x-markdown"
                post.author.id = post.author.uuid
                post.author.host = "http://" + request.get_host() + "/api"
                if len(post.author.github_url) > 0:
                    post.author.github = "http://" + post.author.github_url
                else:
                    post.author.github = post.author.github_url

            posts_serializer = PostsSerializer(posts, many=True)
            response = {
                "query" : "posts",
                "count" : len(final_queryset),
                "size": get_page_size(request, paginator),
                "posts" : posts_serializer.data}
           # Do not return previous if page is 0.
            if (paginator.get_previous_link() is not None):
               response['previous'] = paginator.get_previous_link()

            # Do not return next if last page
            if (paginator.get_next_link() is not None):
                response['next'] = paginator.get_next_link()

            return Response(response)
        except Author.DoesNotExist:
            return Response({'Error': 'The author does not exist.'}, status=status.HTTP_404_NOT_FOUND)

class AuthorViewAllTheirPosts(APIView):
    """
    API endpoint that allows an authenticated user to see all posts from a specific author
    GET /api/author/{author}/posts
    """
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = AuthorPostsPagination

    def get(self, request, auth_id, format=None):
        content = {'user': unicode(request.user), 'auth': unicode(request.auth),}
        try:
            auth_obj = Author.objects.get(uuid=auth_id)
            # all posts except server only posts
            final_queryset = Post.objects.filter(author=auth_obj).exclude(visibility="SERVERONLY").order_by('-created_on')

            paginator = PostsPagination()
            posts = paginator.paginate_queryset(final_queryset, request)
            for post in posts:
                # TODO: Difference in source vs origin?
                post.source = request.scheme + "://" + str(request.META["HTTP_HOST"]) + "/posts/" + str(post.id)
                post.origin = request.scheme + "://" + str(request.META["HTTP_HOST"]) + "/posts/" + str(post.id)
                post.published = post.created_on
                if (post.markdown == False):
                    post.contentType = "text/plain"
                else:
                    post.contentType = "text/x-markdown"
                post.author.id = post.author.uuid
                post.author.host = "http://" + request.get_host() + "/api"
                if len(post.author.github_url) > 0:
                    post.author.github = "http://" + post.author.github_url
                else:
                    post.author.github = post.author.github_url

            posts_serializer = PostsSerializer(posts, many=True)
            response = {
                "query" : "posts",
                "count" : len(final_queryset),
                "size": get_page_size(request, paginator),
                "posts" : posts_serializer.data}
            # Do not return previous if page is 0.
            if (paginator.get_previous_link() is not None):
               response['previous'] = paginator.get_previous_link()
            # Do not return next if last page
            if (paginator.get_next_link() is not None):
                response['next'] = paginator.get_next_link()
            return Response(response)
        except Author.DoesNotExist:
            return Response({'Error': 'Author does not exist.'}, status=status.HTTP_404_NOT_FOUND)

class PostsQuery(APIView):
    """
    API endpoint that gets all posts marked as PUBLIC
    GET /api/posts
    """
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = PostsPagination

    def get(self, request, format=None):
        """
        Return all public posts
        """
        content = {'user': unicode(request.user), 'auth': unicode(request.auth),}

        try:
            # author = Author.objects.get(uuid=authorid)
            # friend_uuids = author.get_all_friend_uuids()
            posts_queryset = Post.objects.filter(visibility="PUBLIC").order_by('-created_on')
            paginator = PostsPagination()
            posts = paginator.paginate_queryset(posts_queryset, request)
            for post in posts:
                # TODO: Difference in source vs origin?
                post.source = request.scheme + "://" + str(request.META["HTTP_HOST"]) + "/posts/" + str(post.id)
                post.origin = request.scheme + "://" + str(request.META["HTTP_HOST"]) + "/posts/" + str(post.id)
                post.published = post.created_on
                if (post.markdown == False):
                    post.contentType = "text/plain"
                else:
                    post.contentType = "text/x-markdown"
                post.author.id = post.author.uuid
                post.author.host = "http://" + request.get_host() + "/api"
                if len(post.author.github_url) > 0:
                    post.author.github = "http://" + post.author.github_url
                else:
                    post.author.github = post.author.github_url


            posts_serializer = PostsSerializer(posts, many=True)
            response = {
                "query" : "posts",
                "count" : len(posts_queryset),
                "size": get_page_size(request, paginator),
                "posts" : posts_serializer.data}
           # Do not return previous if page is 0.
            if (paginator.get_previous_link() is not None):
               response['previous'] = paginator.get_previous_link()

            # Do not return next if last page
            if (paginator.get_next_link() is not None):
                response['next'] = paginator.get_next_link()

            return Response(response)
        except Author.DoesNotExist:
            return Response({'Error': 'Author does not exist'}, status=status.HTTP_404_NOT_FOUND)

class PostIDQuery(APIView):
    """
    API endpoint that sends a single posts info
    GET /api/posts/<postid>
    """
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = PostsPagination

    def get(self, request, post_id, format=None):
        """
        Return a list of the authors friends.
        GET api/posts/<postid>
        """
        content = {'user': unicode(request.user), 'auth': unicode(request.auth),}

        try:
            post = Post.objects.filter(id=post_id).first()
            if (post is None):
                return Response({'Error': 'Post does not exist'}, status=status.HTTP_404_NOT_FOUND)

            # Authentication validation
            # Hindle said the client is responsible for filtering visibility stuff
            if (post.visibility == "PRIVATE" and post.author.user != self.request.user):
                return Response({'Error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
            if (post.visibility == "SERVERONLY"):
                return Response({'Error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

            else:
                # TODO: Difference in source vs origin?
                post.source = request.scheme + "://" + str(request.META["HTTP_HOST"]) + "/posts/" + str(post.id)
                post.origin = request.scheme + "://" + str(request.META["HTTP_HOST"]) + "/posts/" + str(post.id)
                post.published = post.created_on
                if (post.markdown == False):
                    post.contentType = "text/plain"
                else:
                    post.contentType = "text/x-markdown"
                post.author.id = post.author.uuid
                post.author.host = "http://" + request.get_host() +  "/api"
                if len(post.author.github_url) > 0:
                    post.author.github = "http://" + post.author.github_url
                else:
                    post.author.github = post.author.github_url

                posts_serializer = PostsSerializer(post)
                response = {
                    "query" : "posts",
                    "count" : 1,
                    "size": 1,
                    "posts" : posts_serializer.data}

                return Response(response)
        except Author.DoesNotExist:
            return Response({'Error': 'Author does not exist.'}, status=status.HTTP_404_NOT_FOUND)

class CommentsViewSet(APIView):
    """
    Get all comments for a post
    """
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = PostsPagination

    def get(self, request, post_id, format=None):
        """
        Return a list of the post's comments
        GET http://service/posts/<POST_ID>/comments
        """
        content = {'user': unicode(request.user), 'auth': unicode(request.auth),}
        try:
            post = Post.objects.filter(id=post_id).first()
            if (post is None):
                return Response({'Error': 'Post doest not exist.'}, status=status.HTTP_404_NOT_FOUND)

            final_queryset = Comment.objects.filter(parent_post=post).order_by('-created_on')
            paginator = PostsPagination()
            comments = paginator.paginate_queryset(final_queryset, request)
            for commie in comments:
                commie.guid = commie.id
                commie.pubDate = commie.created_on
                commie.author.id = commie.author.uuid
                commie.author.host = "http://" + request.get_host() + "/api"
                commie.author.displayName = commie.author.displayName
                if commie.markdown:
                    commie.contentType = "text/x-markdown"
                else:
                    commie.contentType = "text/plain"

            comments_serializer = SingleCommentSerializer(comments, many=True)
            response = {
                "query" : "comments",
                "count" : len(final_queryset),
                "size": get_page_size(request, paginator),
                "comments" : comments_serializer.data}
            # Do not return previous if page is 0.
            if (paginator.get_previous_link() is not None):
                response['previous'] = paginator.get_previous_link()

            # Do not return next if last page
            if (paginator.get_next_link() is not None):
                response['next'] = paginator.get_next_link()

            return Response(response)
        except Author.DoesNotExist:
            return Response({'Error': 'Author does not exist'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, post_id, format=None):
        """
        Posts to comments to create a comment.
        POST to http://service/posts/<POST_ID>/comments

        Example:
        { "comment": {
                "contentType": "text/plain",
                "published": "2016-11-28T22:15:38.060015Z",
                "author": {
                    "displayName": "admin",
                    "id": "e1f3c310-fdb8-478b-84bb-e0a76fc8889a",
                    "url": "cmput404f16t04dev.herokuapp.com/author/e1f3c310-fdb8-478b-84bb-e0a76fc8889a",
                    "host": "http://cmput404f16t04dev.herokuapp.com",
                    "github": ""
                },
                "comment": "fdbdf",
                "guid": "94e943b9-c0bd-4438-b5b1-12d624ff303a"
                },
            "query": "addComment",
            "post": "http://cmput404f16t04dev2.herokuapp.com/api/posts/1ccc1b7a-4832-45bc-8d92-3b221cc1a073" }
        """
        # Ensure the parent post exists
        parent_post = None
        try:
            parent_post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            print("ADD COMMENT API ERROR: Parent post does not exist.")
            return Response({'Errors': "Parent post does not exist."}, status.HTTP_404_NOT_FOUND)

        """
        CHECK VISIBILITY
        # is_FOAF_remote(viewing_author, remote_author)
        foaf = is_FOAF_str_remote()
        #r = requests.get(comment_host + 'api/friends/', auth=HTTPBasicAuth(n.foreignNodeUser, n.foreignNodePass))
        #friend /api/friends/
        # MAYBE just skip foaf and friend, and return 403 only to private and server only posts!
        # and get the basic posting to work first!!!!! so other teams can test it etc.
        # create a ForeignComment object from received data using ForeignCommentManager
        # Later` in posts_view, retrieve comments & ForeignComment and somehow sort both by time.
        """
        if parent_post.visibility == "SERVERONLY" or  parent_post.visibility == "PRIVATE":
            return Response({"query": "addComment", "success": False, "message":"Comment not allowed"}, status=403)

        # Validate the request data
        serializer = AddForeignCommentSerializer(data=request.data)
        if not serializer.is_valid():
            print serializer.errors
            return Response({'Errors': serializer.errors}, status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        comment_data = data.get('comment')
        author_data = comment_data['author']

        print("\n ADD COMMENT API Recieved Comment Data: ")
        print(comment_data)

        # Get the foreign author
        foreign_author = None
        try:
            foreign_author = ForeignAuthor.objects.get(id=author_data['uuid'])
        except ForeignAuthor.DoesNotExist:
            # Author doesn't exist, so create them in the db.
            # First check if the node exists based off of host.
            node = get_node(author_data['host']) # From utils
            if node:
                foreign_author = ForeignAuthor(id=author_data['uuid'], display_name=author_data['displayName'], node=node)
            else:
                # Node does not exist locally.
                print("ADD COMMENT API ERROR: The node is unknown.")
                return Response({'Errors': "Unknown node"}, status.HTTP_401_UNAUTHORIZED)

        # Create the comment
        fcm = ForeignCommentManager()
        fcm.create_comment(comment_data['id'], foreign_author, parent_post, comment_data['content'], comment_data['created_on'], comment_data['contentType'])
        return Response({"query": "addComment", "success": True, "message":"Comment Added"}, status=200)

class IsFriendQuery(APIView):
    """
    Ask if 2 authors are friends.
    GET http://service/friends/<authorid1>/<authorid2>
    where authorid1 and authorid2 are uuids
    """
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request, authorid1, authorid2, format=None):
        content = {'user': unicode(request.user), 'auth': unicode(request.auth),}
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
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request, authorid, format=None):
        """
        Return a list of the authors friends.
        GET http://service/friends/<authorid>
        """
        content = {'user': unicode(request.user), 'auth': unicode(request.auth),}
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
        content = {'user': unicode(request.user), 'auth': unicode(request.auth),}
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
            if uuid.UUID(friend_id) in friend_uuids:
                matching_uuids.append(friend_id)

        return Response({"query": "friends", "author": authorid, "authors": matching_uuids})

class FriendRequest(APIView):
    """
    POST to http://service/friendrequest
    Author = The user who is receiving the friend request (local author).
    Friend = The user who is making the friend request (remote author).
    """
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request, format=None):
        content = {'user': unicode(request.user), 'auth': unicode(request.auth),}
        # Validate the request data
        serializer = FriendRequestSerializer(data=request.data)
        if not serializer.is_valid():
            print(serializer.errors)
            return Response({'Errors': serializer.errors}, status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        author_data = data.get('author')
        friend_data = data.get('friend')
        print("\n GOT A FRIEND REQUEST THROUGH THE API")
        print(author_data)
        print(friend_data)
        author = None
        friend = None
        # Check that either the author or friend exists locally.
        try:
            author = Author.objects.get(uuid=author_data['id'])
        except Author.DoesNotExist:
            pass
        try:
            friend = Author.objects.get(uuid=friend_data['id'])
        except Author.DoesNotExist:
            pass

        # If neither author is local, we shouldn't be getting the request.
        if (author is None) and (friend is None):
            print("FRIEND REQUEST ERROR: The authors are not local")
            return Response({'Error': 'Neither author is local to this server.'}, status.HTTP_400_BAD_REQUEST)

        # If either author is forgein, we should create them in the db if they are not there already.
        if (author is None):
            if ForeignAuthor.objects.filter(id=author_data['id']).exists():
                author = ForeignAuthor.objects.get(id=author_data['id'])
            else:
                node = None
                try:
                    node = Node.objects.get(url=author_data['host'])
                except Node.DoesNotExist:
                    print("FRIEND REQUEST ERROR WITH AUTHOR NODE")
                    return Response({'\nFRIEND REQUEST ERROR (API) Unknown host in request data.'}, status.HTTP_401_UNAUTHORIZED)
                try:
                    author_url = node.url + '/author/' + str(author_data['id'])
                    author = ForeignAuthor(id=author_data['id'], display_name=author_data['displayName'], node=node, url=author_url)
                    author.save()
                except Exception as error:
                    print("'\nFRIEND REQUEST ERROR (API)" + str(e))
                    return Response({'Message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            # Friend exists on our server. Add the friend to the author's pending foreign friends list.
            if author not in friend.pending_foreign_friends.all():
                friend.pending_foreign_friends.add(author)
            return Response({'Message': 'Friend request received.'}, status=status.HTTP_200_OK)

        if (friend is None):
            if ForeignAuthor.objects.filter(id=friend_data['id']).exists():
                friend = ForeignAuthor.objects.get(id=friend_data['id'])
            else:
                node = None
                try:
                    node = Node.objects.get(url=friend_data['host'])
                except Node.DoesNotExist:
                    print("FRIEND REQUEST ERROR WITH FRIEND NODE")
                    return Response({'\nFRIEND REQUEST ERROR (API) Unknown host in request data.'}, status.HTTP_401_UNAUTHORIZED)
                try:
                    friend = ForeignAuthor(id=friend_data['id'], display_name=friend_data['displayName'], node=node, url=friend_data['url'])
                    friend.save()
                except Exception as error:
                    print("'\nFRIEND REQUEST ERROR (API)" + str(e))
                    return Response({'Message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            # Author exists on our server. Add the friend to the author's pending foreign friends list.
            if friend not in author.pending_foreign_friends.all():
                author.pending_foreign_friends.add(friend)
            return Response({'Message': 'Friend request received.'}, status=status.HTTP_200_OK)

        # If we got here, then both authors are local.
        friend.follow(author)
        return Response(status=status.HTTP_200_OK)

class ProfileView(APIView):

    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, authorid, format=None):
        """
        Return a list of the authors friends.
        GET http://service/friends/<authorid>
        """
        content = {'user': unicode(request.user), 'auth': unicode(request.auth),}
        try:
            author = Author.objects.get(uuid=authorid)
            serializer = ProfileSerializer(author)

            return Response(serializer.data)
        except Author.DoesNotExist:
            return Response({'Error': 'The author does not exist.'}, status=status.HTTP_404_NOT_FOUND)

class ViewApiRawImage(APIView):
    """ After authentication verification it opens image as blob and then
    encode it to base64 and put that in the html.
    """
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request, img, format=None):
        """
        Returns a specific image with given image_id.
        GET http://service/api/media/<image_id>
        """
        content = {'user': unicode(request.user), 'auth': unicode(request.auth),}
        try:
            img_obj = ImageServ.objects.get(pk=img)
            base64obj = "data:" + img_obj.imagetype + ";base64," +  base64.b64encode(img_obj.image)
            return Response({"imagedata": base64obj})
        except:
            return Response({'Error': 'An error happened with retrieving the image.'}, status=status.HTTP_404_NOT_FOUND)
