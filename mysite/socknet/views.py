import datetime

from django.shortcuts import render
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin

from socknet.models import Post

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
    fields = ['content']
    login_url = '/login/' # For login mixin

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super(CreatePost, self).form_valid(form)
