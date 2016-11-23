from socknet.models import *
from rest_framework import serializers

class AuthorPostsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'

class PostsAuthorSerializer(serializers.ModelSerializer):
    """
    Builds Author for PostsSerializer /api/posts
    """
    id = serializers.CharField(max_length = 64)
    host = serializers.CharField(max_length = 128)
    github = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Author
        fields = ('id','host','displayName','url','github')

class PostsCommentsSerializer(serializers.Serializer):
    """
    Builds Comments for PostsSerializer /api/posts
    """
    id = serializers.CharField(max_length=36, required=True) # uuid is 36 characters
    author = serializers.SerializerMethodField()
    comment = serializers.SerializerMethodField()
    contentType = serializers.SerializerMethodField()
    published = serializers.SerializerMethodField()

    def get_author(self, obj):
        author = obj.author
        author.id = author.uuid
        # TODO: Setup host attribute for authors
        author.host = "http://cmput404f16t04dev.herokuapp.com"
        author.github = author.github_url
        serializer = PostsAuthorSerializer(author)
        return serializer.data

    def get_comment(self, obj):
        return obj.content

    def get_contentType(self, obj):
        if (obj.markdown == False):
            return "text/plain"
        else:
            return "text/x-markdown"

    def get_published(self, obj):
        return obj.created_on

class PostsSerializer(serializers.ModelSerializer):
    """
    GET /api/posts/
    """
    source = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    origin = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    contentType = serializers.CharField(max_length = 16)
    author = PostsAuthorSerializer()
    published = serializers.DateTimeField()
    comments = serializers.SerializerMethodField()

    def get_comments(self, obj):
        comments = Comment.objects.all_comments_for_post(obj.id, True)
        serializer = PostsCommentsSerializer(comments, many=True)
        return serializer.data

    def validate_contentType(self, value):
        """
        Checks that the content type is valid
        """
        if value != "text/plain" and value != "text/x-markdown" and value != "text/markdown":
            raise serializers.ValidationError("The content type is not valid. Only text and markdown are accepted.")
        return value

    class Meta:
        model = Post
        exclude = ('created_on', 'imglink', 'markdown')

class AuthorSerializer(serializers.ModelSerializer):
    """
    Serializer for a local author
    uuid, host url, and display name

    UNDER CONSTRUCTION working on figuring out how to get the host url
    """
    id = serializers.CharField(source='uuid', required=True)
    host = serializers.URLField(required=True)
    class Meta:
        model = Author
        fields = ('id', 'displayName', 'host')


class FriendSerializerNoUrl(serializers.Serializer):
    """
    Serializer for an author without url (id, host, displayName)
    Id is an uuid.
    Used in FriendRequestSerializer.F
    """
    id = serializers.CharField(max_length=36, required=True) # uuid is 36 characters
    host = serializers.CharField(max_length=128, required=True)
    displayName = serializers.CharField(max_length=150, required=True)

    def validate_author(self, value):
        """
        Checks that the uuid is valid.
        """
        try:
            valid_uuid = uuid.UUID(value)
        except ValueError:
            raise serializers.ValidationError("UUID is not valid.")
        return value

class FriendSerializer(serializers.Serializer):
    """
    Serializer for an author (id, host, displayName, url)
    Id is an uuid.
    Used in FriendRequestSerializer.
    """
    id = serializers.CharField(max_length=36, required=True) # uuid is 36 characters
    host = serializers.CharField(max_length=128, required=True)
    displayName = serializers.CharField(max_length=150, required=True)
    url = serializers.CharField(max_length=256, required=True)

    def validate_author(self, value):
        """
        Checks that the uuid is valid.
        """
        try:
            valid_uuid = uuid.UUID(value)
        except ValueError:
            raise serializers.ValidationError("UUID is not valid.")
        return value

class FriendsQuerySerializer(serializers.Serializer):
    """
    Serializer for the friend query which asks if anyone in the list is a friend.
    """
    query = serializers.CharField(max_length=32, required=True)
    author = serializers.CharField(max_length=36, required=True) # a uuid is 36 characters
    authors = serializers.ListField(child=serializers.CharField(max_length=36, required=True))

    def validate_query(self, value):
        """
        Check that the query is "friends"
        """
        if value != "friends":
            raise serializers.ValidationError("Query type is not 'friends'.")
        return value

    def validate_author(self, value):
        """
        Checks that the uuid is valid.
        """
        try:
            valid_uuid = uuid.UUID(value)
        except ValueError:
            raise serializers.ValidationError("Author UUID is not valid.")
        return value

class FriendRequestSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=32, required=True)
    author = FriendSerializerNoUrl(required=True)
    friend = FriendSerializer(required=True)

    def validate_query(self, value):
        """
        Check that the query is "friendrequest"
        """
        if value != "friendrequest":
            raise serializers.ValidationError("Query type is not 'friendrequest'.")
        return value

class SingleCommentSerializer(serializers.ModelSerializer):
    """
    Serialize a single comment, used for "get all comments in a post" endpoint.
    This endpoint has different field names than the "get posts for author" comments.
    """
    author = AuthorSerializer(required=True)
    comment = serializers.CharField(source='content', required=True)
    pubDate = serializers.DateTimeField(source='created_on', required=True)
    guid = serializers.CharField(source='id', max_length=36, required=True) # a uuid is 36 characters

    class Meta:
        model = Comment
        fields = ('author', 'guid', 'comment', 'pubDate')


class ProfileFriendSerializer(serializers.Serializer):
    #id = serializers.CharField(max_length = 64) # uuid is 36 characters
    id = serializers.CharField(source='uuid', required =True)
    host = serializers.CharField(max_length=256, required=True)
    displayName = serializers.CharField(max_length=150, required=True)
    url = serializers.CharField(max_length=256, required=True)

    class Meta:
        model = Author
        fields = ('id','host','displayName','url')

class ProfileForeignFriendSerializer(serializers.Serializer):
    id = serializers.CharField(source='uuid', required =True)
    host = serializers.CharField(source = 'node', required=True)
    displayName = serializers.CharField(max_length=150, required=True)
    url = serializers.CharField(max_length=256, required=True)

    class Meta:
        model = ForeignAuthor
        fields = ('id','host','displayName','url')
class ProfileSerializer(serializers.Serializer):
    """
    Serializer for getting a specific authors Profile
    """
    id = serializers.CharField(source='uuid', required=True)
    host = serializers.CharField(max_length = 128)
    displayName = serializers.CharField(max_length=150, required=True)
    url = serializers.CharField(max_length=256, required=True)
    friends = serializers.SerializerMethodField()
    def get_friends(self, obj):
        friends = []
        local_friends = obj.friends.all()
        local_serializer = ProfileFriendSerializer(local_friends,many=True)
        foreign_friends = obj.foreign_friends.all()
        foreign_serializer = ProfileForeignFriendSerializer(foreign_friends,many=True)
        return local_serializer.data+foreign_serializer.data

    class Meta:
        model = Author
        fields = ('id','host','displayName','url')
