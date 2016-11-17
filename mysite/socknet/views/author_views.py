import json
import uuid

from django.shortcuts import get_object_or_404
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from socknet.utils import ForbiddenContent403

from socknet.models import *
from socknet.forms import *

class ViewProfile(LoginRequiredMixin, generic.base.TemplateView):
    """ Displays an Authors profile """
    model= Post
    template_name = "socknet/author_templates/profile.html"
    login_url = '/login/' # For login mixin

    def get_context_data(self, **kwargs):
        context = super(ViewProfile, self).get_context_data(**kwargs)
        authorUUID = self.kwargs.get('authorUUID', self.request.user.author.uuid)
        # Raise 404 if we try to view an author who doesn't exist
        profile_author = get_object_or_404(Author, uuid=authorUUID)
        context['profile_author'] = profile_author
        post_manager = PostManager()
        context['context_list'] = post_manager.get_profile_posts(profile_author, self.request.user.author)

        if authorUUID != self.request.user.author.uuid:
            author = self.request.user.author
            # We are viewing someone elses page, determine what our relationship with
            # them is so we know which relationship button to load (follow, unfollow, ect)
            if profile_author in author.friends.all():
                # They are out friend, display unfriend button
                context['button_action'] = "unfriend"
            elif ((profile_author in author.get_pending_local_friend_requests())
            or (profile_author in author.ignored.all()) and (author in profile_author.who_im_following.all())):
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

class EditProfile(LoginRequiredMixin,generic.edit.UpdateView):
    model = Author
    template_name = "socknet/author_templates/edit_profile.html"
    success_url='/'
    login_url = '/login/' # For login mixin
    form_class = EditProfileForm

    def get(self, request, *args, **kwargs):
        # First, get the authors UUID from the url
        authorUUID = self.kwargs.get('authorUUID', self.request.user.author)
        # Convert uuid from into a proper UUID field (otherwise it will be unicode or something)
        authorUUID = uuid.UUID(authorUUID)
        # Check if the logged in user's uuid matches the one we got from the url
        if authorUUID != self.request.user.author.uuid:
            return ForbiddenContent403.denied()
        return super(EditProfile, self).get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        obj = Author.objects.get(uuid=self.kwargs['authorUUID'])
        return obj

    def get_context_data(self, **kwargs):
        context = super(EditProfile, self).get_context_data(**kwargs)
        authorUUID = self.kwargs.get('authorUUID', self.request.user.author.uuid)
        # Raise 404 if we try to view an author who doesn't exist
        profile_author = get_object_or_404(Author, uuid=authorUUID)
        context['profile_author'] = profile_author
        return context

class ManageFriends(LoginRequiredMixin, generic.base.TemplateView):
    """ Displays an Author's friends and allow them to manage their friends """
    template_name = "socknet/author_templates/manage_friends.html"
    login_url = '/login/' # For login mixin

    def get(self, request, *args, **kwargs):
        authorUUID = self.kwargs.get('authorUUID', self.request.user.author)
        # Convert uuid from url into a proper UUID field
        authorUUID = uuid.UUID(authorUUID)
        if authorUUID != self.request.user.author.uuid:
            return ForbiddenContent403.denied()
        return super(ManageFriends, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        authorUUID = self.kwargs.get('authorUUID', self.request.user.author)
        # Convert uuid from url into a proper UUID field
        authorUUID = uuid.UUID(authorUUID)
        # Ensure that someone else is not trying to edit our friends
        if authorUUID != self.request.user.author.uuid:
            return ForbiddenContent403.denied()
        if request.is_ajax():
            decoded_json = json.loads(request.body)
            action_type = decoded_json['action']
            friend_uuid = decoded_json['friend']['id']
            is_local = decoded_json['friend']['is_local']
            friend = None
            if is_local:
                friend = Author.objects.get(uuid=friend_uuid)
            else:
                friend = ForeignAuthor.objects.get(id=friend_uuid)
            author = request.user.author
            if action_type == "unfriend":
                author.delete_friend(friend, is_local)
                return HttpResponse(status=200)
            elif action_type == "unfollow":
                author.unfollow(friend)
                return HttpResponse(status=200)
            elif action_type == "follow":
                author.follow(friend)
                return HttpResponse(status=200)
            elif action_type == "accept_friend_request":
                author.accept_friend_request(friend_uuid, is_local)
                return HttpResponse(status=200)
            else:
                print("MANAGE FRIEND POST: Unknown action")
                return HttpResponse(status=500)

class ManageFollowing(LoginRequiredMixin, generic.base.TemplateView):
    """ Manage who an author is following """
    template_name = "socknet/author_templates/manage_following.html"
    login_url = '/login/' # For login mixin

    def get(self, request, *args, **kwargs):
        authorUUID = self.kwargs.get('authorUUID', self.request.user.author)
        # Convert uuid from url into a proper UUID field
        authorUUID = uuid.UUID(authorUUID)
        if authorUUID != self.request.user.author.uuid:
            return ForbiddenContent403.denied()
        return super(ManageFollowing, self).get(request, *args, **kwargs)

class ManageFriendRequests(LoginRequiredMixin, generic.base.TemplateView):
    """ Accept and decline pending friend requests """
    template_name = "socknet/author_templates/manage_friend_requests.html"
    login_url = '/login/' # For login mixin

    def get_context_data(self, **kwargs):
        # Get all friend requests for a user.
        context = super(ManageFriendRequests, self).get_context_data(**kwargs)
        pending_requests = self.request.user.author.get_pending_friend_requests()
        context['pending_requests'] = pending_requests
        context['count'] = len(pending_requests)
        return context

    def get(self, request, *args, **kwargs):
        authorUUID = self.kwargs.get('authorUUID', self.request.user.author)
        # Convert uuid from url into a proper UUID field
        authorUUID = uuid.UUID(authorUUID)
        if authorUUID != self.request.user.author.uuid:
            return ForbiddenContent403.denied()
        return super(ManageFriendRequests, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        authorUUID = self.kwargs.get('authorUUID', self.request.user.author)
        # Convert uuid from url into a proper UUID field
        authorUUID = uuid.UUID(authorUUID)
        # Ensure that someone else is not trying to edit our friends
        if authorUUID != self.request.user.author.uuid:
            return ForbiddenContent403.denied()
        if request.is_ajax():
            decoded_json = json.loads(request.body)
            print(decoded_json)
            action_type = decoded_json['action']
            friend_uuid = decoded_json['friend']['id']
            is_local = decoded_json['friend']['is_local']
            friend = None
            if is_local:
                friend = Author.objects.get(uuid=friend_uuid)
            else:
                friend = ForeignAuthor.objects.get(id=friend_uuid)
            author = request.user.author
            if action_type == "decline_friend_request":
                author.decline_friend_request(friend_uuid, is_local)
                return HttpResponse(status=200)
            elif action_type == "accept_friend_request":
                author.accept_friend_request(friend_uuid, is_local)
                return HttpResponse(status=200, content=author.get_pending_friend_request_count())
            else:
                return HttpResponse(status=500)
