from django.test import TestCase
from model_mommy import mommy
from rest_framework.test import APITestCase, APIClient
from socknet.models import *
import json

class FriendAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Make a local author
        self.user = mommy.make(User)
        self.author = mommy.make(Author, user=self.user)

        # Make a foreign author
        self.node = mommy.make(Node, name="Test Node", url="http://test-node.com")
        self.foreign_author = mommy.make(ForeignAuthor, node=self.node)

        # Make the client
        self.client = APIClient()

    def test_double_friend_query(self):
        """
        GET http://service/friends/<authorid1>/<authorid2>
        Test when the authors are friends.
        """
        self.author.foreign_friends.add(self.foreign_author)
        url = "/api/friends/%s/%s/" % (self.author.uuid, self.foreign_author.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        decoded_json = json.loads(response.content)
        # Check that the response data matches what we expect
        self.assertEquals(decoded_json['query'], "friends", "Query has the incorrect type.")
        self.assertTrue(decoded_json['friends'], "Query returned false when authors are friends.")
        self.assertEquals(decoded_json['authors'][0], str(self.author.uuid), "uuid is incorrect for author1")
        self.assertEquals(decoded_json['authors'][1], str(self.foreign_author.id), "uuid is incorrect for author2")

    def test_double_friends_query_404(self):
        """
        GET http://service/friends/<authorid1>/<authorid2>
        Test when the authors do not exist.
        """
        url = "/api/friends/%s/%s/" % ("test123", "test456")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
