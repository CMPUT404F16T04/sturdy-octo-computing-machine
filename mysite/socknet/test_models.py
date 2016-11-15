#!/usr/bin/python
# -*- coding: utf-8 -*-
# Taken from https://www.python.org/dev/peps/pep-0263/
# Taken from https://www.python.org/dev/peps/pep-0414/
from __future__ import unicode_literals
from model_mommy import mommy
from django.test import TestCase
from django.contrib.auth.models import User

from socknet.models import *
from socknet.forms import *

class PostsTests(TestCase):

    def _is_plaintext_safe(self, model_to_test):
        """ Test if plaintext is safe: converts < > to &lt; &gt; etc.
        Additionally ignores \n it does not convert that to <br/>
        because the templates which use "linebreaksbr" already take care of that.
        """
        test_content = '#testing<b>\nno'
        test_expect = '#testing&lt;b&gt;<br/>no'
        model = model_to_test
        model.content = test_content
        model.markdown = False
        self.assertEqual(model.view_content(), test_expect)

    def _is_markdown(self, model_to_test):
        """ Tests markdown if it works, i.e. changes # to <h1> and still ignores
        the \n since not needed due to html template's "linebreaksbr"
        """
        test_content = '# testing\n<b>\n>test-block'
        test_expect = '<h1>testing</h1><br/><p>&lt;b&gt;</p><br/><blockquote><br/><p>test-block</p><br/></blockquote><br/>'
        model = model_to_test
        model.content = test_content
        model.markdown = True
        # Content is converted to markdown on viewing.
        self.assertEqual(model.view_content(), test_expect)
        # Content inside post is actually still original.
        self.assertEqual(model.content, test_content)

    def _accepts_weird_characters(self, model_to_test):
        lennyeh = unicode("( ͡° ͜ʖ ͡°) \n¯\_ツ_/¯")
        lenny_result = unicode("( ͡° ͜ʖ ͡°) <br/>¯\_ツ_/¯")
        model = model_to_test
        model.content = lennyeh
        model.markdown = False
        self.assertEqual(model.view_content(), lenny_result)

    def test_posts(self):
        model = Post()
        self._is_plaintext_safe(model)
        self._is_markdown(model)
        self._accepts_weird_characters(model)

    def test_comments(self):
        model = Comment()
        self._is_plaintext_safe(model)
        self._is_markdown(model)
        self._accepts_weird_characters(model)

class AuthorTests(TestCase):
    def setUp(self):
        # Create local authors
        self.user1 = mommy.make(User, username="user1")
        self.user2 = mommy.make(User, username="user2")
        self.author1 = mommy.make(Author, user=self.user1)
        self.author2 = mommy.make(Author, user=self.user2)

        # Create foreign author
        self.node = mommy.make(Node, name="Test Node", url="http://test-node.com")
        self.foreign_author = mommy.make(ForeignAuthor, node=self.node)

    def test_create(self):
        self.assertTrue(isinstance(self.author1, Author))
        # uuid should be generated for us
        self.assertTrue(self.author1.uuid)
        # Author has no relationships when first created
        self.assertQuerysetEqual(self.author1.friends.all(), [])
        self.assertQuerysetEqual(self.author1.who_im_following.all(), [])
        self.assertQuerysetEqual(self.author1.ignored.all(), [])

    def test_follow(self):
        # Test that follow is not bi-directional
        self.assertQuerysetEqual(self.author1.who_im_following.all(), [])
        self.author1.follow(self.author2)
        self.assertQuerysetEqual(self.author1.who_im_following.all(), ['<Author: user2>'])
        self.assertQuerysetEqual(self.author1.my_followers.all(), [])
        self.author1.unfollow(self.author2)
        self.assertQuerysetEqual(self.author1.who_im_following.all(), [])

    def test_pending_friend_request_with_ignore(self):
        # No friend requests
        self.assertQuerysetEqual(self.author1.get_pending_friend_requests(), [])
        self.author2.follow(self.author1)
        # 1 pending friend request b/c author 2 followed me
        self.assertQuerysetEqual(self.author1.get_pending_friend_requests(), ['<Author: user2>'])
        self.author1.ignored.add(self.author2)
        # No friend requests because I ignored it
        self.assertQuerysetEqual(self.author1.get_pending_friend_requests(), [])

    def test_pending_friend_request_with_friend(self):
        self.author2.follow(self.author1)
        # 1 pending friend request
        self.assertQuerysetEqual(self.author1.get_pending_friend_requests(), ['<Author: user2>'])
        self.author1.accept_friend_request(self.author2)
        # No friend requests because we accepted it
        self.assertQuerysetEqual(self.author1.get_pending_friend_requests(), [])

    def test_accept_friend_request(self):
        self.author2.follow(self.author1)
        # Only a follower so far
        self.assertQuerysetEqual(self.author1.my_followers.all(), ['<Author: user2>'])
        # We shouldn't be friends and I'm not following them yet
        self.assertQuerysetEqual(self.author1.who_im_following.all(), [])
        self.assertQuerysetEqual(self.author1.friends.all(), [])
        self.author1.accept_friend_request(self.author2)
        # Since we accepted the friend request we should be a follower of our friend
        self.assertQuerysetEqual(self.author1.who_im_following.all(), ['<Author: user2>'])
        # Our friend should still be a follower
        self.assertQuerysetEqual(self.author1.my_followers.all(), ['<Author: user2>'])
        # We should both be friends too
        self.assertQuerysetEqual(self.author1.friends.all(), ['<Author: user2>'])
        self.assertQuerysetEqual(self.author2.friends.all(), ['<Author: user1>'])

    def test_delete_friend(self):
        self.author2.follow(self.author1)
        self.author1.accept_friend_request(self.author2)
        self.assertQuerysetEqual(self.author1.friends.all(), ['<Author: user2>'])
        self.assertQuerysetEqual(self.author1.my_followers.all(), ['<Author: user2>'])
        self.assertQuerysetEqual(self.author1.who_im_following.all(), ['<Author: user2>'])
        # Delete our friend
        self.author1.delete_friend(self.author2, True)
        # We should no longer be friends
        self.assertQuerysetEqual(self.author1.friends.all(), [])
        # We are no longer following our recently deleted friend
        self.assertQuerysetEqual(self.author1.who_im_following.all(), [])
        # Our friend is still following us
        self.assertQuerysetEqual(self.author1.my_followers.all(), ['<Author: user2>'])

    def test_is_friend_local(self):
        """
        Test is_friend method for a local friend.
        """
        self.author2.follow(self.author1)
        self.author1.accept_friend_request(self.author2)
        # We are friends
        self.assertTrue(self.author1.is_friend(self.author2.uuid))
        self.author1.delete_friend(self.author2, True)
        # We are not longer friends
        self.assertFalse(self.author1.is_friend(self.author2.uuid))

    def test_is_friend_foreign(self):
        """
        Test is_friend method for a foreign friend.
        """
        self.author1.foreign_friends.add(self.foreign_author)
        # We are friends
        self.assertTrue(self.author1.is_friend(self.foreign_author.id))
        self.author1.foreign_friends.remove(self.foreign_author)
        self.assertFalse(self.author1.is_friend(self.foreign_author.id))

    def test_get_all_friends(self):
        self.author1.foreign_friends.add(self.foreign_author)
        self.author2.follow(self.author1)
        self.author1.accept_friend_request(self.author2)
        # Author has 2 friends
        friend_uuids = self.author1.get_all_friend_uuids()
        self.assertTrue((self.author2.uuid in friend_uuids), "The local friend uuid is missing")
        self.assertTrue((self.foreign_author.id in friend_uuids), "The foreign friend uuid is missing")
