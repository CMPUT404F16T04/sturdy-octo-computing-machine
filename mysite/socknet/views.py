import json
import uuid

from django.shortcuts import render
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied

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
        post_pk = Post(id=self.kwargs.get('post_pk', self.request.user.author.uuid))
        context['profile_author'] = Author.objects.get(uuid=authorUUID)
        return context
        
    def form_valid(self, form):
        print str(self.post_pk)
        form.instance.author = self.request.user.author
        form.instance.parent = Post(id=self.kwargs.get('post_pk', self.request.user.author.uuid))
        return super(CreateComment, self).form_valid(form)
        
class ViewProfile(LoginRequiredMixin, generic.base.TemplateView):
    """ Displays an Authors profile """
    template_name = "socknet/profile.html"
    login_url = '/login/' # For login mixin

    def get_context_data(self, **kwargs):
        context = super(ViewProfile, self).get_context_data(**kwargs)
        authorUUID = self.kwargs.get('authorUUID', self.request.user.author.uuid)
        context['profile_author'] = Author.objects.get(uuid=authorUUID)
        return context

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            # We are sending ajax POSTs from "follow" button
            decodedJson = json.loads(request.body)
            friend_uuid = decodedJson['friend']['id']
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
        print("Manage Friends... checking permissions")
        authorUUID = self.kwargs.get('authorUUID', self.request.user.author)
        # Convert uuid from url into a proper UUID field
        authorUUID = uuid.UUID(authorUUID)
        if authorUUID != self.request.user.author.uuid:
            raise PermissionDenied
        print("Permissions OK")
        return super(ManageFriends, self).get(request, *args, **kwargs)
