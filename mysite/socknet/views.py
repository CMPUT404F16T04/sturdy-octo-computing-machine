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

class ListPosts(LoginRequiredMixin, generic.ListView):
    """ Displays a list of all posts in the system """
    model = Post
    template_name = 'socknet/list_posts.html'
    login_url = '/login/' # For login mixin

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

class ViewComments(LoginRequiredMixin, generic.ListView):
    """ Displays a list of all comments for the post
    How to use foreign keys in URL taken from Michael http://stackoverflow.com/a/18533475
    """
    model = Comment
    post_pk = Post
    template_name = 'socknet/list_comments.html'
    login_url = '/login/' # For login mixin

class ViewComment(LoginRequiredMixin, generic.ListView):
    """ Displays a specific comment for the post
    How to use foreign keys in URL taken from Michael http://stackoverflow.com/a/18533475
    """
    model = Comment
    post_pk = Post
    template_name = 'socknet/comment.html'
    login_url = '/login/' # For login mixin

class CreateComment(LoginRequiredMixin, generic.edit.CreateView):
    """ Displays a form for creating a new comment """
    model = Comment
    template_name = 'socknet/create_comment.html'
    fields = ['content', 'markdown']
    login_url = '/login/' # For login mixin
    post_pk = 0

    def get_context_data(self, **kwargs):
        context = super(CreateComment, self).get_context_data(**kwargs)
        #form.instance.post_id = Post(id=116)
        post_pk = Post(id=self.kwargs.get('post_pk'))
        post_obj = get_object_or_404(Post, id=post_pk)
        context['comments'] = post_obj
        return context

    def form_valid(self, form):
        print str(self.post_pk)
        form.instance.author = self.request.user.author
        form.instance.parent = Post(id=self.kwargs.get('post_pk', self.request.user.author.uuid))
        return super(CreateComment, self).form_valid(form)

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
            x = profile_author in author.get_pending_friend_requests()
            y = profile_author in author.friends.all()
            z = profile_author in author.who_im_following.all()
            print("Is in friends? "+str(y))
            print("Is in pending FR? "+str(x))
            print("Am i following? "+str(z))
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
