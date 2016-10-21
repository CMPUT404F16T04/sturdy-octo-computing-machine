from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
import uuid
from socknet.utils import HTMLsafe

class Author(models.Model):
    """
    Represents an author

    Friends, followers, and friend Requests need to be designed such that:
    - Querying for friends or followers is quick
    - Friends of friends is easy to compute
    - It is easy to decline friend requests
    - Querying pending friend requests is quick
    """
    user = models.OneToOneField(User)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    # Friends and followers are separate --> I can be both a friend and a follower
    # ignored is for friend requests you have declined, just means it won't show up as pending
    friends = models.ManyToManyField("self", related_name="my_friends", blank=True)
    who_im_following = models.ManyToManyField("self", related_name="my_followers", symmetrical=False, blank=True)
    ignored = models.ManyToManyField("self", related_name="ignored_by", symmetrical=False, blank=True)

    def __str__(self):
        return self.user.get_username()

    def get_pending_friend_requests(self):
        """ Returns my pending friend requests
        (people who have followed me, but I have not followed them) """
        pending = self.my_followers.all()
        pending = pending.exclude(pk__in=self.ignored.all()) # ignored requests we have declined
        pending = pending.exclude(pk__in=self.friends.all()) # ignored people we are already friends with
        return pending

    def accept_friend_request(self, requester):
        """
        When a friend request is accepted, both authors will be considered
        followers AND friends of each other.
        """
        if requester not in self.my_followers.all():
            # Stale state, should probably reload the page
            raise ValueError("Attempted to accept friend request when requester is no longer following me!")
        if requester not in self.friends.all():
            self.friends.add(requester)
        if requester not in self.who_im_following.all():
            self.who_im_following.add(requester)
        self.save()
        return

    def decline_friend_request(self, requester):
        """
        When we decline a friend request we simply move the requester into
        our ignored queue (all this means is it won't show up in our friend requests).
        """
        self.ignored.add(requester)
        self.save()
        return

    def delete_friend(self, friend):
        """ When we remove a friend, we unfriend and unfollow them. """
        self.friends.remove(friend)
        self.who_im_following.remove(friend)
        self.save()
        return

    def follow(self, friend):
        self.who_im_following.add(friend)
        friend.save()

    def unfollow(self, friend):
        self.who_im_following.remove(friend)
        friend.save()

    def get_following_only(self):
        """ Get who I am following excluding friends """
        following = self.who_im_following.all()
        following = following.exclude(pk__in=self.friends.all())
        return following


class Post(models.Model):
    """ Represents a post made by a user """
    author = models.ForeignKey(Author, related_name="author")
    content = models.TextField(max_length=512)
    created_on = models.DateTimeField(auto_now=True)
    markdown = models.BooleanField()

    def get_absolute_url(self):
        """ Gets the canonical URL for a Post
        Will be of the format .../posts/<id>/
        """
        return reverse('view_post', args=[str(self.id)])

    def view_content(self):
        """ Retrieves content to be displayed as html, it is assumed safe
        due to HTMLsafe's get_converted_content() applies HTML escapes already.
        """
        return HTMLsafe.get_converted_content(self.markdown, self.content)

    # enable weird characters like lenny faces taken from:
    #http://stackoverflow.com/questions/36389723/why-is-django-using-ascii-instead-of-utf-8
    def __unicode__(self):
        return self.author.user.username + ": " + self.content

class Comment(models.Model):
    """ Represents a comment made by a user """
    parent = models.ForeignKey(Post, related_name="parent_post")
    author = models.ForeignKey(Author, related_name="comment_author")
    content = models.TextField(max_length=512)
    created_on = models.DateTimeField(auto_now=True)
    markdown = models.BooleanField()

    def get_absolute_url(self):
        """ Gets the canonical URL for a Post
        Will be of the format .../posts/<id>/comment/<id>
        """
        return reverse('view_comment', args=[str(self.parent.id), str(self.id)])

    def view_content(self):
        """ Retrieves content to be displayed as html, it is assumed safe
        due to HTMLsafe's get_converted_content() applies HTML escapes already.
        """
        return HTMLsafe.get_converted_content(self.markdown, self.content)

    # enable weird characters like lenny faces taken from:
    #http://stackoverflow.com/questions/36389723/why-is-django-using-ascii-instead-of-utf-8
    def __unicode__(self):
        return self.author.user.username + ": " + self.content
