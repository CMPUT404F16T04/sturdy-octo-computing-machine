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
    github = serializers.CharField()

    class Meta:
        model = Author
        fields = ('id','host','displayName','url','github')

class PostsCommentsSerializer(serializers.Serializer):
    """
    Builds Comments for PostsSerializer /api/posts
    """
    id = serializers.CharField(max_length=36, required=True) # uuid is 36 characters
    author = serializers.CharField(max_length=128, required=True)

class PostsSerializer(serializers.ModelSerializer):
    """
    GET /api/posts/
    """
    source = serializers.URLField()
    origin = serializers.URLField()
    contentType = serializers.CharField(max_length = 16)
    author = PostsAuthorSerializer()
    comments = serializers.SerializerMethodField()

    def get_comments(self, obj):
        comments = Comment.objects.all_comments_for_post(obj.id, True)
        print(comments)
        serializer = PostsCommentsSerializer(comments, many=True)
        return serializer.data

    class Meta:
        model = Post
        fields = '__all__'

class AuthorSerializerNoURL(serializers.Serializer):
    """
    Serializer for an author without url (id, host, displayName)
    Id is an uuid.
    Used in FriendRequestSerializer.
    """
    id = serializers.CharField(max_length=36, required=True) # uuid is 36 characters
    host = serializers.CharField(max_length=128, required=True)
    display_name = serializers.CharField(max_length=150, required=True)

    def validate_author(self, value):
        """
        Checks that the uuid is valid.
        """
        try:
            valid_uuid = uuid.UUID(value)
        except ValueError:
            raise serializers.ValidationError("UUID is not valid.")
        return value

    def validate_host(self, value):
        node = Node.objects.filter(url=value).exists()
        if not node:
            raise serializers.ValidationError('Unknown host: %s' % value)
        return value

class AuthorSerializer(serializers.Serializer):
    """
    Serializer for an author (id, host, displayName, url)
    Id is an uuid.
    Used in FriendRequestSerializer.
    """
    id = serializers.CharField(max_length=36, required=True) # uuid is 36 characters
    host = serializers.CharField(max_length=128, required=True)
    display_name = serializers.CharField(max_length=150, required=True)
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

    def validate_host(self, value):
        node = Node.objects.filter(url=value).exists()
        if not node:
            raise serializers.ValidationError('Unknown host: %s' % value)
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
    author = AuthorSerializerNoURL(required=True)
    friend = AuthorSerializer(required=True)

    def validate_query(self, value):
        """
        Check that the query is "friendrequest"
        """
        if value != "friendrequest":
            raise serializers.ValidationError("Query type is not 'friendrequest'.")
        return value
