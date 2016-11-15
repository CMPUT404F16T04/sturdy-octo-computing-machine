from django.test import TestCase
from model_mommy import mommy
from rest_framework.test import APITestCase, APIClient
from socknet.models import *
import json
import uuid

class FriendAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Make some local authors
        self.user = mommy.make(User)
        self.user2 = mommy.make(User)
        self.author = mommy.make(Author, user=self.user)
        self.author2 = mommy.make(Author, user=self.user2)

        # Make a foreign author
        self.node = mommy.make(Node, name="Test Node", url="http://test-node.com")
        self.foreign_author = mommy.make(ForeignAuthor, node=self.node)

        # Make the client
        self.client = APIClient()

        # Make a UUID for testing garbage data
        self.uuid = uuid.UUID('{00000123-0101-0101-0101-000000001234}')
        self.uuid2 = uuid.UUID('{00000123-0101-0101-0101-000000005555}')

    def test_is_friend_query(self):
        """
        GET http://service/friends/<authorid1>/<authorid2>
        Test when the authors are friends.
        """
        self.author.foreign_friends.add(self.foreign_author)
        url = "/api/friends/%s/%s/" % (self.author.uuid, self.foreign_author.id)
        response = self.client.get(url)
        decoded_json = json.loads(response.content)
        # Check that the response data matches what we expect
        self.assertEqual(response.status_code, 200)
        self.assertEquals(decoded_json['query'], "friends", "Query has the incorrect type.")
        self.assertTrue(decoded_json['friends'], "Query returned false when authors are friends.")
        self.assertEquals(decoded_json['authors'][0], str(self.author.uuid), "uuid is incorrect for author1")
        self.assertEquals(decoded_json['authors'][1], str(self.foreign_author.id), "uuid is incorrect for author2")

    def test_is_friends_query_404(self):
        """
        GET http://service/friends/<authorid1>/<authorid2>
        Test when the authors do not exist.
        """
        url = "/api/friends/%s/%s/"  % (str(self.uuid), str(self.uuid2))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_friends_query(self):
        """
        GET http://service/friends/<authorid>
        """
        self.author.foreign_friends.add(self.foreign_author)
        self.author.friends.add(self.author2)
        url = "/api/friends/%s/" % self.author.uuid
        response = self.client.get(url)
        decoded_json = json.loads(response.content)
        # Check that the response data matches what we expect
        self.assertEqual(response.status_code, 200)
        self.assertEquals(decoded_json['query'], "friends", "Query has the incorrect type.")
        self.assertTrue((str(self.author2.uuid) in decoded_json['authors']), "Local friend is missing from list.")
        self.assertTrue((str(self.foreign_author.id) in decoded_json['authors']), "Foreign friend is missing from list.")

    def test_friends_query_404(self):
        """
        GET http://service/friends/<authorid>
        Test when the authorid does not exist.
        """
        url = "/api/friends/%s/" % str(self.uuid)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_friend_query_post(self):
        """
        POST http://service/friends/<authorid>
        """
        # Setup our authors friends
        self.author.foreign_friends.add(self.foreign_author)
        self.author.friends.add(self.author2)
        # Create the request data. Contains 2 friends and 1 garbage uuid.
        authors = [str(self.foreign_author.id), str(self.uuid), str(self.author2.uuid)]
        request_data = json.dumps({"query": "friends", "author": str(self.author.uuid), "authors": authors})
        # Make the request
        url = "/api/friends/%s/" % self.author.uuid
        response = self.client.post(url, data=request_data, content_type='application/json')
        decoded_json = json.loads(response.content)
        # Check that the response data matches what we expect
        self.assertEqual(response.status_code, 200)
        self.assertEquals(decoded_json['query'], "friends", "Query has the incorrect type.")
        self.assertEquals(decoded_json['author'], str(self.author.uuid), "The author uuid is incorrect.")
        self.assertTrue((str(self.author2.uuid) in decoded_json['authors']), "Local friend is missing from list.")
        self.assertTrue((str(self.foreign_author.id) in decoded_json['authors']), "Foreign friend is missing from list.")
        self.assertTrue((str(self.uuid) not in decoded_json['authors']), "Garbage uuid was in the list.")
