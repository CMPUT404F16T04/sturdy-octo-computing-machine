from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from socknet.utils import HTMLsafe
# for images auto delete
from django.db.models.signals import pre_delete
from django.dispatch import receiver
import uuid
from itertools import chain

class Node(models.Model):
    """
    Represents a server we can communicate with
    """
    name = models.CharField(max_length=32) # A name for a host. (Ex) socknet
    url = models.CharField(max_length=128, unique="True")

    def __str__(self):
        return self.name

class ForeignAuthor(models.Model):
    """
    Represents an author from another node
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node = models.ForeignKey(Node, related_name="my_node")

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

    # Friend stuff for forgein authors
    foreign_friends = models.ManyToManyField(ForeignAuthor, related_name="my_foreign_friends", blank=True)
    pending_foreign_friends = models.ManyToManyField(ForeignAuthor, related_name="my_pending_foreign_friend_requests", blank=True)

    # Profile fields
    github_url = models.TextField(blank=True)
    about_me = models.CharField(max_length=1000, blank=True)
    birthday = models.DateField(null=True,blank=True)

    def __str__(self):
        return self.user.get_username()

    def is_friend(self, author_uuid):
        """
        Checks if an author is this author's friend.
        Checks both local and foreign friend lists.
        """
        is_friend = self.friends.filter(uuid=author_uuid).exists()
        if not is_friend:
            # If author is not a local friend, check if they are a foreign friend
            is_friend = self.foreign_friends.filter(id=author_uuid).exists()
        return is_friend

    def get_pending_friend_requests(self):
        """ Returns my pending friend requests
        (people who have followed me, but I have not followed them)
        """
        # TODO: UPDATE FOR FOREIGN FRIENDS
        pending = self.my_followers.all()
        pending = pending.exclude(pk__in=self.ignored.all()) # ignored requests we have declined
        pending = pending.exclude(pk__in=self.friends.all()) # ignored people we are already friends with
        return pending

    def accept_friend_request(self, requester):
        """
        When a friend request is accepted, both authors will be considered
        followers AND friends of each other.
        """
        # TODO: UPDATE FOR FOREIGN FRIENDS
        if requester not in self.my_followers.all():
            # Stale state, should probably reload the page
            raise ValueError("Attempted to accept friend request when requester is no longer following me!")
        if requester not in self.friends.all():
            self.friends.add(requester)
        if requester not in self.who_im_following.all():
            self.who_im_following.add(requester)
        if requester in self.ignored.all():
            # If we had them ignored previously, we are friends now
            self.ignored.remove(requester)
        self.save()
        return

    def decline_friend_request(self, requester):
        """
        When we decline a friend request we simply move the requester into
        our ignored queue (all this means is it won't show up in our friend requests).
        """
        # TODO: UPDATE FOR FOREIGN FRIENDS
        self.ignored.add(requester)
        self.save()
        return

    def delete_friend(self, friend, is_local):
        """
        Deletes both local and foreign friends.
        Local: When we remove a friend, we unfriend and unfollow them.
        """
        if is_local:
            # Remove a local friend
            self.friends.remove(friend)
            self.who_im_following.remove(friend)
            self.save()
        else:
            # Remove a foreign friend
            self.foreign_friends.remove(friend)
            self.save()
        return

    def follow(self, friend):
        # TODO: UPDATE FOR FOREIGN FRIENDS
        self.who_im_following.add(friend)
        if friend in self.ignored.all():
            # If we had them ignored previously, we are following them now
            self.ignored.remove(friend)
        self.save()

    def unfollow(self, friend):
        # TODO: UPDATE FOR FOREIGN FRIENDS
        self.who_im_following.remove(friend)
        self.save()

    def get_following_only(self):
        """ Get who I am following excluding friends """
        # TODO: UPDATE FOR FOREIGN FRIENDS
        following = self.who_im_following.all()
        following = following.exclude(pk__in=self.friends.all())
        return following

class Post(models.Model):
    """ Represents a post made by a user """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(Author, related_name="author")
    title = models.CharField(max_length=64, default="No Title")
    description = models.CharField(max_length=128, default="No description provided.")
    content = models.TextField(max_length=512)
    created_on = models.DateTimeField(auto_now=True)
    markdown = models.BooleanField()
    imglink = models.CharField(max_length=256)
    visibility = models.CharField(default='PUBLIC', max_length=255, choices=[
        ('PUBLIC', 'PUBLIC'),
        ('FOAF', 'FOAF'),
        ('FRIENDS', 'FRIENDS'),
        ('PRIVATE', 'PRIVATE'),
        ('SERVERONLY', 'SERVERONLY')])

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

    def getFullEnglishVisibility(self):
        ''' Gets the full, written out English phrase
        for the visibility string'''
        if (self.visibility == 'PUBLIC'):
            return 'Public'
        elif (self.visibility == 'FOAF'):
            return 'Friend of Friends'
        elif (self.visibility == 'FRIENDS'):
            return 'Friends'
        elif (self.visibility == 'PRIVATE'):
            return 'Private'
        elif (self.visibility == 'SERVERONLY'):
            return 'Server Only'
        else:
            return 'Unknown'

    # enable weird characters like lenny faces taken from:
    #http://stackoverflow.com/questions/36389723/why-is-django-using-ascii-instead-of-utf-8
    def __unicode__(self):
        return self.author.user.username + ": " + self.content

class PostManager(models.Model):

    def get_profile_posts(self, profile_author, current_author):
        """
        Returns the posts to display when viewing someone's profile.

        FOAF and Server Only are NOT implemented yet.
        """
        # If someone is viewing their own page, they can see all posts
        if profile_author == current_author:
            return Post.objects.filter(author=profile_author).order_by('-created_on')

        public_posts = Post.objects.filter(author=profile_author, visibility='PUBLIC')
        friend_posts = {}
        foaf_posts = {} # TODO IMPLEMENT FOAF
        server_only_posts = {} # TODO IMPLEMENT SERVER ONLY

        if current_author in profile_author.friends.all():
            friend_posts = Post.objects.filter(author=profile_author, visibility='FRIENDS')

        # Combine the query sets, sort by most recent
        visible_posts = sorted(
            chain(public_posts, friend_posts, foaf_posts, server_only_posts),
            key=lambda instance: instance.created_on, reverse=True)

        return visible_posts

class CommentQuerySet(models.QuerySet):
    """ Query operations for the Comments table. """
    def all_comments_for_post(self, post_pk, ordered):
        # Retrieve only post specific comments
        results = self.filter(parent_post_id=post_pk)
        # Order it with latest date on top
        if(ordered):
            results = results.order_by('-created_on',)
        return results

    def comments_count_post(self, post_pk):
        result = self.filter(parent_post_id=post_pk).count()
        return results

    def all_comments_for_author(self, author_pk, ordered):
        # Retrieve only post specific comments
        results = self.filter(author_id=author_pk)
        # Order it with latest date on top
        if(ordered):
            results = results.order_by('-created_on',)
        return results

class Comment(models.Model):
    """ Represents a comment made by a user """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    objects = CommentQuerySet.as_manager()
    # Should really use model inheritance, found out about it too late though, https://docs.djangoproject.com/en/1.10/topics/db/models/#model-inheritance
    parent_post = models.ForeignKey(Post, related_name="comment_parent_post")
    author = models.ForeignKey(Author, related_name="comment_author")
    content = models.TextField(max_length=512)
    created_on = models.DateTimeField(auto_now=True)
    markdown = models.BooleanField()

    def get_absolute_url(self):
        """ Gets the canonical URL for a Post
        Will be of the format .../posts/<id>/comment/<id>
        """
        # This aint even in the user stories. Could skip???
        #return reverse('view_comment', args=[str(self.id)])

        # Redirects to previous list of comments with the anchor of the created post.
        #return reverse('list_comments_anchor', args=[str(self.parent_post.id), str(self.id)]).replace('%23', '#')
        return reverse('view_post', args=[str(self.parent_post.id)])

    def view_content(self):
        """ Retrieves content to be displayed as html, it is assumed safe
        due to HTMLsafe's get_converted_content() applies HTML escapes already.
        """
        return HTMLsafe.get_converted_content(self.markdown, self.content)

    # enable weird characters like lenny faces taken from:
    #http://stackoverflow.com/questions/36389723/why-is-django-using-ascii-instead-of-utf-8
    def __unicode__(self):
        return "Parent post:"+ str(self.parent_post.id) + ", Author:" + self.author.user.username + ": " + self.content

class ImageManager(models.Manager):
    """ Helps creating an image object.
    Taken from https://docs.djangoproject.com/en/1.10/ref/models/instances/#creating-objects
    """
    def create_image(self, img, au, pst):
        img = self.create(image=img, author=au, parent_post=pst)
        return img

class ImageServ(models.Model):
    """ Represents an image uploaded by the user. """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to='user_images', max_length=256)
    author = models.ForeignKey(Author, related_name="image_author")
    parent_post = models.ForeignKey(Post, related_name="image_parent_post")
    created_on = models.DateTimeField(auto_now=True)
    objects = ImageManager()

    def ImageServ(self, image, author, parent_post):
        self.image = image
        self.author = author
        self.parent_post = parent_post

    # Django does not remove images automatically anymore upon DB removal.
    # Taken from darrinm http://stackoverflow.com/a/14310174
    # automatically remove image that was removed in DB
    @receiver(pre_delete)
    def ImageServ_delete(sender, instance, **kwargs):
        # Pass false so FileField doesn't save the model.
        if type(instance) == ImageServ:
            instance.image.delete(False)

    def get_absolute_url(self):
        """ Gets the canonical URL for an image.
        Will be of the format .../images/<id>/comment/<id>
        """
        return reverse('view_image', args=[str(self.image)])

    def __unicode__(self):
        return "Author:" + self.author.user.username + " : " + str(self.image)
