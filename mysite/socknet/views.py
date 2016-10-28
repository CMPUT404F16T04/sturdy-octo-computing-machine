import json
import uuid

from django.shortcuts import get_object_or_404
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy
from socknet.models import *
# For images
import os
from mysite.settings import MEDIA_ROOT
from PIL import Image, ImageFile
import base64
from django.core.exceptions import ValidationError


class ListPosts(LoginRequiredMixin, generic.ListView):
    """ Displays a list of all posts in the system """
    model = Post
    template_name = 'socknet/list_posts.html'
    login_url = '/login/' # For login mixin

    def get_context_data(self, **kwargs):
        context = super(ListPosts, self).get_context_data(**kwargs)
        context['posts_list'] = Post.objects.order_by('-created_on')
        return context

class ViewPost(LoginRequiredMixin, generic.detail.DetailView):
    """ Displays the details of a single post """
    model = Post
    template_name = 'socknet/view_post.html'
    login_url = '/login/' # For login mixin

class CreatePost(LoginRequiredMixin, generic.edit.CreateView):
    """ Displays a form for creating a new post """
    model = Post
    template_name = 'socknet/create_post.html'
    fields = ['content', 'markdown']
    login_url = '/login/' # For login mixin

    def form_valid(self, form):
        # If there was an image, make image object
        # https://docs.djangoproject.com/en/1.10/ref/request-response/#django.http.HttpRequest
        if not self.request.FILES == {}:
            try:
                # taken from Dtephen Paulger http://stackoverflow.com/a/20762344
                Image.open(self.request.FILES['image']).verify()
            except IOError:
                raise ValidationError("Unsupported file type. Upload an image type please.", code='invalid')
            img = ImageServ.objects.create_image(self.request.FILES['image'], self.request.user.author, form.instance)
            form.instance.imglink = img.image
        else:
            form.instance.imglink = ""
        form.instance.author = self.request.user.author
        return super(CreatePost, self).form_valid(form)

class DeletePost(LoginRequiredMixin, generic.edit.DeleteView):
    """ Displays a form for deleting posts  """
    model = Post
    template_name = 'socknet/author_check_delete.html'
    login_url = '/login/' # For login mixin
    success_url=('/')

    def form_valid(self, form):
        return super(DeletePost, self).form_valid(form)

class ListComments(LoginRequiredMixin, generic.ListView):
    """ Displays a list of all comments for the post
    """
    model = Comment
    template_name = 'socknet/list_comments.html'
    login_url = '/login/' # For login mixin

    def get_context_data(self, **kwargs):
        context = super(ListComments, self).get_context_data(**kwargs)
        parent_post = Post(id=self.kwargs.get('post_pk'))
        context['parent'] = parent_post
        context['comments'] = Comment.objects.all_comments_for_post(parent_post.id, True)
        return context

class ViewComment(LoginRequiredMixin, generic.base.TemplateView):
    """ Displays a specific comment for the post
    """
    model = Comment
    template_name = 'socknet/comment.html'
    login_url = '/login/' # For login mixin

    def get_context_data(self, **kwargs):
        context = super(ViewComment, self).get_context_data(**kwargs)
        # Todo: why does it not load the comment object properly?!
        # This causes the comment view page to crash! aaa. it does not load contents, nor authorm nor parent_post!
        comment_obj = Comment(id=self.kwargs.get('pk'))
        print(comment_obj.id)
        post_obj = Post(id=comment_obj.parent_post)
        context['parent_id'] = post_obj
        context['comment'] = comment_obj
        return context

class CreateComment(LoginRequiredMixin, generic.edit.CreateView):
    """ Displays a form for creating a new comment """
    model = Comment
    template_name = 'socknet/create_comment.html'
    fields = ['content', 'markdown']
    login_url = '/login/' # For login mixin

    def get_context_data(self, **kwargs):
        context = super(CreateComment, self).get_context_data(**kwargs)
        parent_key = self.kwargs.get('post_pk')
        post_obj = get_object_or_404(Post, id=parent_key)
        context['comments'] = post_obj
        return context

    def form_valid(self, form):
        form.instance.author = self.request.user.author
        parent_key = (self.kwargs.get('post_pk'))
        form.instance.parent_post = Post(id=parent_key)
        return super(CreateComment, self).form_valid(form)

class ViewImage(LoginRequiredMixin, generic.base.TemplateView):
    """ Get the normal image view. """
    model= ImageServ
    template_name = "socknet/image.html"
    login_url = '/login/' # For login mixin
    def get_context_data(self, **kwargs):
        context = super(ViewImage, self).get_context_data(**kwargs)
        parent_key = self.kwargs.get('img')
        context['image_loc'] = get_object_or_404(ImageServ, image=parent_key)
        return context

class ViewRawImage(LoginRequiredMixin, generic.base.TemplateView):
    """ After authentication verification it opens image as blob and then
    encode it to base64 and put that in the html.
    """
    model= ImageServ
    template_name = "socknet/imager.html"
    login_url = '/login/' # For login mixin
    def get_context_data(self, **kwargs):
        context = super(ViewRawImage, self).get_context_data(**kwargs)
        parent_key = self.kwargs.get('img')
        filetype = parent_key.split('.')[-1]
        path = os.path.join(MEDIA_ROOT, parent_key)
        blob = open(path, 'rb')
        context['b64'] = "data:image/" + filetype + ";base64," + base64.b64encode(blob.read())
        return context

class ViewProfile(LoginRequiredMixin, generic.base.TemplateView):
    """ Displays an Authors profile """
    model= Post
    template_name = "socknet/profile.html"
    login_url = '/login/' # For login mixin

    def get_context_data(self, **kwargs):
        context = super(ViewProfile, self).get_context_data(**kwargs)
        authorUUID = self.kwargs.get('authorUUID', self.request.user.author.uuid)
        # Raise 404 if we try to view an author who doesn't exist
        profile_author = get_object_or_404(Author, uuid=authorUUID)
        context['profile_author'] = profile_author
        context['context_list'] = Post.objects.all()

        if authorUUID != self.request.user.author.uuid:
            author = self.request.user.author
            # We are viewing someone elses page, determine what our relationship with
            # them is so we know which relationship button to load (follow, unfollow, ect)
            if profile_author in author.friends.all():
                # They are out friend, display unfriend button
                context['button_action'] = "unfriend"
            elif profile_author in author.get_pending_friend_requests():
                # We aren't friends, but they are following me
                context['button_action'] = "accept_friend_request"
            elif profile_author in author.who_im_following.all():
                # We are following them, display unfollow button
                context['button_action'] = "unfollow"
            else:
                # No relationship, display follow button
                context['button_action'] = "follow"

        return context

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            # We are sending ajax POSTs from "follow" button
            decoded_json = json.loads(request.body)
            friend_uuid = decoded_json['friend']['id']
            friend = Author.objects.get(uuid=friend_uuid)
            return HttpResponse(status=200)
        else:
            # Returning 500 right now since nothing else should be posting to this page
            return HttpResponse(status=500)

class ManageFriends(LoginRequiredMixin, generic.base.TemplateView):
    """ Displays an Author's friends and allow them to manage their friends """
    template_name = "socknet/manage_friends.html"
    login_url = '/login/' # For login mixin

    def get(self, request, *args, **kwargs):
        authorUUID = self.kwargs.get('authorUUID', self.request.user.author)
        # Convert uuid from url into a proper UUID field
        authorUUID = uuid.UUID(authorUUID)
        if authorUUID != self.request.user.author.uuid:
            raise PermissionDenied
        return super(ManageFriends, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        authorUUID = self.kwargs.get('authorUUID', self.request.user.author)
        # Convert uuid from url into a proper UUID field
        authorUUID = uuid.UUID(authorUUID)
        # Ensure that someone else is not trying to edit our friends
        if authorUUID != self.request.user.author.uuid:
            raise PermissionDenied
        if request.is_ajax():
            decoded_json = json.loads(request.body)
            action_type = decoded_json['action']
            friend_uuid = decoded_json['friend']['id']
            friend = Author.objects.get(uuid=friend_uuid)
            author = request.user.author
            if action_type == "unfriend":
                print("Unfriending " + friend.user.username)
                author.delete_friend(friend)
                return HttpResponse(status=200)
            elif action_type == "unfollow":
                print("Unfollowing " + friend.user.username)
                author.unfollow(friend)
                return HttpResponse(status=200)
            elif action_type == "follow":
                print("Following " + friend.user.username)
                author.follow(friend)
                return HttpResponse(status=200)
            elif action_type == "accept_friend_request":
                print("Accepting Friend Request of: " + friend.user.username)
                author.accept_friend_request(friend)
                return HttpResponse(status=200)
            else:
                print("MANAGE FRIEND POST: Unknown action")
                return HttpResponse(status=500)

class ManageFollowing(LoginRequiredMixin, generic.base.TemplateView):
    """ Manage who an author is following """
    template_name = "socknet/manage_following.html"
    login_url = '/login/' # For login mixin

    def get(self, request, *args, **kwargs):
        authorUUID = self.kwargs.get('authorUUID', self.request.user.author)
        # Convert uuid from url into a proper UUID field
        authorUUID = uuid.UUID(authorUUID)
        if authorUUID != self.request.user.author.uuid:
            raise PermissionDenied
        return super(ManageFollowing, self).get(request, *args, **kwargs)

class ManageFriendRequests(LoginRequiredMixin, generic.base.TemplateView):
    """ Accept and decline pending friend requests """
    template_name = "socknet/manage_friend_requests.html"
    login_url = '/login/' # For login mixin

    def get(self, request, *args, **kwargs):
        authorUUID = self.kwargs.get('authorUUID', self.request.user.author)
        # Convert uuid from url into a proper UUID field
        authorUUID = uuid.UUID(authorUUID)
        if authorUUID != self.request.user.author.uuid:
            raise PermissionDenied
        return super(ManageFriendRequests, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        authorUUID = self.kwargs.get('authorUUID', self.request.user.author)
        # Convert uuid from url into a proper UUID field
        authorUUID = uuid.UUID(authorUUID)
        # Ensure that someone else is not trying to edit our friends
        if authorUUID != self.request.user.author.uuid:
            raise PermissionDenied
        if request.is_ajax():
            decoded_json = json.loads(request.body)
            action_type = decoded_json['action']
            friend_uuid = decoded_json['friend']['id']
            friend = Author.objects.get(uuid=friend_uuid)
            author = request.user.author
            if action_type == "decline_friend_request":
                print("Decling Friend Request of: " + friend.user.username)
                author.decline_friend_request(friend)
                return HttpResponse(status=200)
            elif action_type == "accept_friend_request":
                print("Accepting Friend Request of: " + friend.user.username)
                author.accept_friend_request(friend)
                return HttpResponse(status=200, content=len(author.get_pending_friend_requests()))
            else:
                print("MANAGE FRIEND REQUEST POST: Unknown action")
                return HttpResponse(status=500)
