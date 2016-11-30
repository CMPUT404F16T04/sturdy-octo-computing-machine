from django.test import TestCase
from model_mommy import mommy
from rest_framework.test import APITestCase, APIClient
from socknet.models import *
from socknet.serializers import *
import json
import uuid
import datetime

class FriendAPITests(APITestCase):
    def setUp(self):
        # Make some local authors
        self.user = mommy.make(User)
        self.user2 = mommy.make(User)
        self.author = mommy.make(Author, user=self.user)
        self.author2 = mommy.make(Author, user=self.user2)

        # Make a foreign author
        self.node = mommy.make(Node, name="Test Node", url="http://test-node.com")
        self.foreign_author = mommy.make(ForeignAuthor, node=self.node)

        # Our node
        self.local_node = mommy.make(Node, name="Localhost", url="http://127.0.0.1:8000")

        # Make the client
        self.client = APIClient()

        # Make a UUID for testing garbage data
        self.uuid = uuid.UUID('{00000123-0101-0101-0101-000000001234}')
        self.uuid2 = uuid.UUID('{00000123-0101-0101-0101-000000005555}')

        # Authentication
        self.client.force_authenticate(user=self.user)

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

    def test_friend_query_post_404(self):
        """
        POST http://service/friends/<authorid>
        Test when author does not exist.
        """
        authors = [str(self.foreign_author.id)]
        request_data = json.dumps({"query": "friends", "author": str(self.uuid), "authors": authors})
        url = "/api/friends/%s/" % str(self.uuid)
        response = self.client.post(url, data=request_data, content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_friend_query_post_bad_request(self):
        """
        POST http://service/friends/<authorid>
        Test when query type is wrong.
        """
        # Create the request data. Contains 2 friends and 1 garbage uuid.
        authors = [str(self.author2.uuid)]
        request_data = json.dumps({"query": "test", "author": str(self.author.uuid), "authors": authors})
        # Make the request
        url = "/api/friends/%s/" % self.author.uuid
        response = self.client.post(url, data=request_data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_friend_query_post_bad_uuid(self):
        """
        POST http://service/friends/<authorid>
        Test when author uuid is bad.
        """
        # Create the request data. Contains 2  friends and 1 garbage uuid.
        authors = [str(self.author2.uuid)]
        request_data = json.dumps({"query": "friends", "author": '{00000123-0101-0101-0101-000000005}', "authors": authors})
        # Make the request
        url = "/api/friends/%s/" % self.uuid
        response = self.client.post(url, data=request_data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_friend_request_local(self):
        """
        POST http://service/friendrequest
        Both authors are local.
        """
        # Confirm no pending request
        self.assertTrue(len(self.author.get_pending_friend_requests()) is 0)
        # Create the request data
        author = {"id": str(self.author.uuid), "host": self.local_node.url, "displayName": "Bob"}
        friend = {"id": str(self.author2.uuid), "host": self.local_node.url, "displayName": "Joe", "url": self.local_node.url+"/"+str(self.author2.uuid)}
        request_data = json.dumps({"query": "friendrequest", "author": author, "friend": friend})
        # Make the request
        url = "/api/friendrequest/"
        response = self.client.post(url, data=request_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        # Confirm friend request is pending
        self.assertTrue(self.author in self.author2.who_im_following.all())
        self.assertTrue(len(self.author.get_pending_friend_requests()) is 1)

    def test_friend_request_foreign_friend(self):
        """
        POST http://service/friendrequest
        Friend who is sending the request is foreign.
        Author receiving the request is local.
        """
        # Confirm no pending request
        self.assertFalse(self.foreign_author in self.author.pending_foreign_friends.all())
        # Create the request data
        author = {"id": str(self.author.uuid), "host": self.local_node.url, "displayName": "Bob"}
        friend = {"id": str(self.foreign_author.id), "host": self.node.url, "displayName": "Joe", "url": self.node.url+"/"+str(self.author2.uuid)}
        request_data = json.dumps({"query": "friendrequest", "author": author, "friend": friend})
        # Make the request
        url = "/api/friendrequest/"
        response = self.client.post(url, data=request_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        # Confirm friend request is pending
        self.assertTrue(self.foreign_author in self.author.pending_foreign_friends.all())

    def test_friend_request_foreign_author(self):
        """
        POST http://service/friendrequest
        Friend who is sending the request is local.
        Author receiving the request is foreign.
        """
        # TODO
        pass

class PostsAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient(HTTP_HOST='127.0.0.1:8000')

        self.user = mommy.make(User)
        self.author = mommy.make(Author, user=self.user)

        self.client.force_authenticate(user=self.user)

    def test_posts(self):
        """
        GET  http://service/posts
        """

        self.post = mommy.make(Post,
                               author=self.author,
                               title="Example Title",
                               content="Example Content.",
                               markdown=False)
        url = "/api/posts/"
        response = self.client.get(url)
        decoded_json = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(decoded_json['posts'][0]['title'], "Example Title", "Post title does not match.")
        self.assertEqual(decoded_json['posts'][0]['description'], "No description provided.", "Post description does not match.")
        self.assertEqual(decoded_json['posts'][0]['content'], "Example Content.", "Post content does not match.")
        self.assertEqual(decoded_json['posts'][0]['visibility'], "PUBLIC", "Post visibility does not match.")
        self.assertEqual(decoded_json['posts'][0]['categories'], "N/A", "Post categories does not match.")

    def test_author_posts(self):
        """
        GET http://service/author/posts
        """

        self.user2 = mommy.make(User)
        self.author2 = mommy.make(Author, user=self.user2)

        self.post = mommy.make(Post,
                               author=self.author2,
                               title="Example Title",
                               content="Example Content.",
                               markdown=False,
                               visibility="PRIVATE")

        url = "/api/author/posts"
        response = self.client.get(url)
        decoded_json = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(decoded_json['posts'][0]['title'], "Example Title", "Post title does not match.")
        self.assertEqual(decoded_json['posts'][0]['description'], "No description provided.", "Post description does not match.")
        self.assertEqual(decoded_json['posts'][0]['content'], "Example Content.", "Post content does not match.")
        # As per eClass post, filtering is responsibility of client
        # https://eclass.srv.ualberta.ca/mod/forum/discuss.php?d=734704
        self.assertEqual(decoded_json['posts'][0]['visibility'], "PRIVATE", "Post visibility does not match.")
        self.assertEqual(decoded_json['posts'][0]['categories'], "N/A", "Post categories does not match.")

    def test_author_author_id_posts(self):
        """
        GET http://service/author/{AUTHOR_ID}/posts
        """

        self.user2 = mommy.make(User)
        self.author2 = mommy.make(Author, user=self.user2)

        uuid = self.author.uuid
        uuid2 = self.author2.uuid

        self.post = mommy.make(Post,
                               author=self.author2,
                               title="Example Title",
                               content="Example Content.",
                               markdown=False,
                               visibility="PRIVATE")

        # Try with a different author's UUID, should not see the post
        url = "/api/author/" + str(uuid) + "/posts/"
        response = self.client.get(url)
        decoded_json = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(decoded_json['posts'], "Should not see any posts for this author")

        # Try with the post's author's UUID, should see the post
        url = "/api/author/" + str(uuid2) + "/posts/"
        response = self.client.get(url)
        decoded_json = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(decoded_json['posts'][0]['title'], "Example Title", "Post title does not match.")
        self.assertEqual(decoded_json['posts'][0]['description'], "No description provided.", "Post description does not match.")
        self.assertEqual(decoded_json['posts'][0]['content'], "Example Content.", "Post content does not match.")
        # As per eClass post, filtering is responsibility of client
        # https://eclass.srv.ualberta.ca/mod/forum/discuss.php?d=734704
        self.assertEqual(decoded_json['posts'][0]['visibility'], "PRIVATE", "Post visibility does not match.")
        self.assertEqual(decoded_json['posts'][0]['categories'], "N/A", "Post categories does not match.")

    def test_posts_post_id(self):
        """
        GET http://service/posts/{POST_ID}
        """


        self.post = mommy.make(Post,
                               author=self.author,
                               title="Example Title",
                               content="Example Content.",
                               markdown=False,
                               visibility="PRIVATE")

        # Try post ID that doesn't exist, should not see post
        url = "/api/posts/" + str(self.author.uuid) + "/"
        response = self.client.get(url)
        decoded_json = json.loads(response.content)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(decoded_json['Error'], "Post does not exist")

        # Try post ID that does exist, should not see post
        url = "/api/posts/" + str(self.post.id) + "/"
        response = self.client.get(url)
        decoded_json = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(decoded_json['posts']['title'], "Example Title", "Post title does not match.")
        self.assertEqual(decoded_json['posts']['description'], "No description provided.", "Post description does not match.")
        self.assertEqual(decoded_json['posts']['content'], "Example Content.", "Post content does not match.")
        # As per eClass post, filtering is responsibility of client
        # https://eclass.srv.ualberta.ca/mod/forum/discuss.php?d=734704
        self.assertEqual(decoded_json['posts']['visibility'], "PRIVATE", "Post visibility does not match.")
        self.assertEqual(decoded_json['posts']['categories'], "N/A", "Post categories does not match.")

class ProfileAPITests(APITestCase):
    def setUp(self):
        # Make some local authors
        self.user = mommy.make(User)
        self.user2 = mommy.make(User)
        self.author = mommy.make(Author, user=self.user)
        self.author2 = mommy.make(Author, user=self.user2)

        # Make the client
        self.client = APIClient()

         # Make a foreign author
        self.node = mommy.make(Node, name="Test Node", url="http://test-node.com")
        self.foreign_author = mommy.make(ForeignAuthor, node=self.node)

        # Our node
        self.local_node = mommy.make(Node, name="Localhost", url="http://127.0.0.1:8000")

        # Make a UUID for testing garbage data
        self.uuid = uuid.UUID('{00000123-0101-0101-0101-000000002222}')
        self.uuid2 = uuid.UUID('{00000123-0101-0101-0101-000000004444}')

        # Authentication
        self.client.force_authenticate(user=self.user)

    def test_profiles(self):
        """
        GET http://service/author/authorid
        """
        self.author.foreign_friends.add(self.foreign_author)
        self.author.friends.add(self.author2)

        url = "/api/author/%s/"  % (str(self.author.uuid))
        response = self.client.get(url)
        decoded_json = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(decoded_json['id'],str(self.author.uuid),"Id sent did not match author UUID")
        self.assertEqual(decoded_json['friends'][0]['id'],str(self.author2.uuid),"Local Friend is being sent incorrectly")
        self.assertEqual(decoded_json['friends'][1]['id'],str(self.foreign_author.id),"Foreign Friend is being sent incorrectly")

class CommentAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient(HTTP_HOST='127.0.0.1:8000')

        #Make a fake user
        self.user = mommy.make(User)
        self.node = mommy.make(Node, name="Test Node", url="http://test-node.com")
        self.author = mommy.make(Author, user=self.user)

        #Make example Post
        self.post = mommy.make(Post,
                               author=self.author,
                               title="Example Title",
                               content="Example Content.",
                               markdown=False)

        #Make example comment
        self.comment = mommy.make(Comment,
                                 parent_post=self.post,
                                 author = self.author,
                                 content = "Example Comment")

        self.client.force_authenticate(user=self.user)

        self.uuid = uuid.UUID('{00000123-0101-0101-0101-000000001234}')

    def test_comment_get(self):
        """
        GET http://service/api/posts/postID/comments/
        """

        url = "/api/posts/%s/comments/" % (str(self.post.id))
        response = self.client.get(url)
        decoded_json = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(decoded_json['query'],"comments","Query was incorrect")
        self.assertEqual(decoded_json['comments'][0]["comment"],"Example Comment","Comment text was incorrect")
        self.assertEqual(decoded_json['comments'][0]['author']['id'],str(self.author.uuid),"Author Id was incorrect")


    def test_comment_post(self):
        """
        POST http://service/api/posts/postID/comments/
        """
        cmt = {
            "author":{
               # ID of the Author (UUID)
               "id": str(self.author.uuid),
               "host": self.node.url,
               "displayName": self.author.displayName,
               # url to the authors information
               "url": self.author.url,
               # HATEOS url for Github API
               "github": self.author.github_url
            },
            "comment":"Test Comment",
            "contentType": "text/plain",
            # ISO 8601 TIMESTAMP
            "published": str(datetime.datetime.utcnow().isoformat()) + "Z",
            # ID of the Comment (UUID)
            "guid": str(uuid.uuid4())
        }
        add = {
            "query" : "addComment",
            "post" : "http://test.com/posts",
            "comment" : cmt
            }
        request_data = json.dumps(add)
        url = "/api/posts/%s/comments/" % str(self.post.id)
        response = self.client.post(url, data=request_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        decoded_json = json.loads(response.content)
        self.assertEqual(decoded_json['query'], "addComment", "Query was incorrect")
        self.assertEqual(decoded_json['message'], "Comment Added", "Message was incorrect")
        self.assertTrue(decoded_json['success'], "Success should have been true.")
