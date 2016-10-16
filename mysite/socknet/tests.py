#!/usr/bin/python
# -*- coding: utf-8 -*-
# Taken from https://www.python.org/dev/peps/pep-0263/
# Taken from https://www.python.org/dev/peps/pep-0414/
from __future__ import unicode_literals
from django.test import TestCase
from django.contrib.auth.models import User

from socknet.models import *

class PostsTests(TestCase):

    def test_is_plaintext_safe(self):
        """ Test if plaintext is safe: converts < > to &lt; &gt; etc.
        Additionally ignores \n it does not convert that to <br/>
        because the templates which use "linebreaksbr" already take care of that.
        """
        test_content = '#testing<b>\nno'
        test_expect = '#testing&lt;b&gt;<br/>no'
        model = Post()
        model.content = test_content
        model.markdown = False
        self.assertEqual(model.view_content(), test_expect)

    def test_is_markdown(self):
        """ Tests markdown if it works, i.e. changes # to <h1> and still ignores
        the \n since not needed due to html template's "linebreaksbr"
        """
        test_content = '# testing\n<b>\n>test-block'
        test_expect = '<h1>testing</h1><br/><p>&lt;b&gt;</p><br/><blockquote><br/><p>test-block</p><br/></blockquote><br/>'
        model = Post()
        model.content = test_content
        model.markdown = True
        # Content is converted to markdown on viewing.
        self.assertEqual(model.view_content(), test_expect)
        # Content inside post is actually still original.
        self.assertEqual(model.content, test_content)

    def test_accepts_weird_characters(self):
        lennyeh = unicode("( ͡° ͜ʖ ͡°) \n¯\_ツ_/¯")
        lenny_result = unicode("( ͡° ͜ʖ ͡°) <br/>¯\_ツ_/¯")
        model = Post()
        model.content = lennyeh
        model.markdown = False
        self.assertEqual(model.view_content(), lenny_result)

class AuthorTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user('user1', 'user1@email.ca', 'user1')
        self.user2 = User.objects.create_user('user2', 'user2@email.ca', 'user2')
        self.author1 = Author(user=self.user1)
        self.author1.save()
        self.author2 = Author(user=self.user2)
        self.author2.save()

    def test_create(self):
        self.assertTrue(isinstance(self.author1, Author))
        # uuid should be generated for us
        self.assertTrue(self.author1.uuid)
        # Author has no relationships when first created
        self.assertQuerysetEqual(self.author1.friends.all(), [])
        self.assertQuerysetEqual(self.author1.followers.all(), [])
        self.assertQuerysetEqual(self.author1.ignore.all(), [])

    def test_follow(self):
        # Test that follow is not bi-directional
        self.assertQuerysetEqual(self.author1.followers.all(), [])
        self.author1.followers.add(self.author2)
        self.assertQuerysetEqual(self.author1.followers.all(), ['<Author: user2>'])
        self.assertQuerysetEqual(self.author1.follower_of.all(), [])

    def test_pending_friend_request_with_ignore(self):
        # No friend requests
        self.assertQuerysetEqual(self.author1.get_pending_friend_requests(), [])
        self.author1.followers.add(self.author2)
        # 1 pending friend request
        self.assertQuerysetEqual(self.author1.get_pending_friend_requests(), ['<Author: user2>'])
        self.author1.ignore.add(self.author2)
        # No friend requests because we ignored it
        self.assertQuerysetEqual(self.author1.get_pending_friend_requests(), [])

    def test_pending_friend_request_with_friend(self):
        self.author1.followers.add(self.author2)
        # 1 pending friend request
        self.assertQuerysetEqual(self.author1.get_pending_friend_requests(), ['<Author: user2>'])
        self.author1.accept_friend_request(self.author2)
        # No friend requests because we accepted it
        self.assertQuerysetEqual(self.author1.get_pending_friend_requests(), [])

    def test_accept_friend_request(self):
        self.author1.followers.add(self.author2)
        self.assertQuerysetEqual(self.author1.follower_of.all(), [])
        # Only a follower so far
        self.assertQuerysetEqual(self.author1.friends.all(), [])
        self.author1.accept_friend_request(self.author2)
        # Since we accepted the friend request we should be a follower of our friend
        self.assertQuerysetEqual(self.author1.follower_of.all(), ['<Author: user2>'])
        # Our friend should still be a follower
        self.assertQuerysetEqual(self.author1.followers.all(), ['<Author: user2>'])
        # We should both be friends too
        self.assertQuerysetEqual(self.author1.friends.all(), ['<Author: user2>'])
        self.assertQuerysetEqual(self.author2.friends.all(), ['<Author: user1>'])

    def test_delete_friend(self):
        self.author1.followers.add(self.author2)
        self.author1.accept_friend_request(self.author2)
        self.assertQuerysetEqual(self.author1.friends.all(), ['<Author: user2>'])
        self.assertQuerysetEqual(self.author1.follower_of.all(), ['<Author: user2>'])
        # Delete our friend
        self.author1.delete_friend(self.author2)
        # We should no longer be friends
        self.assertQuerysetEqual(self.author1.friends.all(), [])
        # We are no longer following our recently deleted friend
        self.assertQuerysetEqual(self.author1.follower_of.all(), [])
        # Our friend is still following us
        self.assertQuerysetEqual(self.author1.followers.all(), ['<Author: user2>'])
