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
    class Meta:
        model = Author
        fields = '__all__'

class FriendsQuerySerializer(serializers.Serializer):
    """
    Serializer for the friend query which asks if anyone in the list is a friend.
    """
    query = serializers.CharField(max_length=100, required=True)
    author = serializers.CharField(max_length=100, required=True) # a uuid is 36 characters
    authors = serializers.ListField(child=serializers.CharField(max_length=100, required=True))

    def validate_query(self, value):
        """
        Check that the query is "friends"
        """
        if value != "friends":
            print(value)
            raise serializers.ValidationError("Query type is not 'friends'.")
        return value
