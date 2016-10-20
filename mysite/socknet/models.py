from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import html
import CommonMark
import HTMLParser
import uuid

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
        Will be of the format .../post/<id>/
        """
        return reverse('view_post', args=[str(self.id)])

    def _unescape_markdown(self, text):
        """ Removes HTML escape characters from given text for <code> tags
        in markdown to work properly: any contents within the <code></code> tags
        gets decoded. Then returns the result.

        """
        tmp = text
        # Anything within <code></code> will be decoded.
        parser = HTMLParser.HTMLParser()
        # Split by the commonmark generated tags (they're not user generated).
        tmp = tmp.split('<')
        starts = 0
        ends = 0
        code_tag_contents = []
        for each in tmp:
            if each.replace(' ','').startswith('code>'):
                starts += 1
            if each.replace(' ','').startswith('/code>'):
                ends += 1
            # if currently within a <code> tag, decode html escape chars.
            if starts > ends:
                code_tag_contents.append(parser.unescape(each))
            else:
                code_tag_contents.append(each)
        return '<'.join(code_tag_contents)

    def get_converted_content(self):
        """ Converts and returns the instance's content appropriately whether post
        is in markdown or in plain text. It escapes user generated content first before
        applying markdown (if applicable) and returning it.
        """
        safe_text = html.conditional_escape(self.content)
        if self.markdown:
            # To enable block quotes in markdown.
            mark = safe_text.replace('&gt;', '>')
            mark = CommonMark.commonmark(mark)
            markdowned = self._unescape_markdown(mark)
            return markdowned.replace('\n', '<br/>')
        return safe_text.replace('\n', '<br/>')

    def view_content(self):
        """ Retrieves content to be displayed as html, it is assumed safe
        due to get_converted_content() applies HTML escapes already.
        """
        return self.get_converted_content()

    # enable weird characters like lenny faces taken from:
    #http://stackoverflow.com/questions/36389723/why-is-django-using-ascii-instead-of-utf-8
    def __unicode__(self):
        return self.author.user.username + ": " + self.content
