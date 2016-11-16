from socknet.models import *
from rest_framework import serializers

class AuthorPostsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'

class PostsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'

class AuthorSerializer(serializers.ModelSerializer):
    """
    Serializer for an author (id, host, displayName, url)
    Where id is an uuid.
    """
    host = serializers.CharField(max_length=128, required=True)


class FriendsQuerySerializer(serializers.Serializer):
    """
    Serializer for the friend query which asks if anyone in the list is a friend.
    """
    query = serializers.CharField(max_length=64, required=True)
    author = serializers.CharField(max_length=64, required=True) # a uuid is 36 characters
    authors = serializers.ListField(child=serializers.CharField(max_length=64, required=True))

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
