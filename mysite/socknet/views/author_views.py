import json
import uuid
import requests
from requests.auth import HTTPBasicAuth

from django.shortcuts import get_object_or_404
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from socknet.utils import ForbiddenContent403

from socknet.models import *
from socknet.forms import *
from socknet.serializers import ProfileSerializer

class ViewProfile(LoginRequiredMixin, generic.base.TemplateView):
    """ Displays an Authors profile """
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

    def get_context_data(self, **kwargs):
        # Get all friend of a user.
        context = super(ManageFriends, self).get_context_data(**kwargs)
        friends = self.request.user.author.get_friends()
        context['friends'] = friends
        context['count'] = len(friends)
        return context

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
                return HttpResponse(status=200,  content=friend_uuid)
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

class ViewRemoteProfile(LoginRequiredMixin, generic.base.TemplateView):
    """ Display a remote author's profile """
    template_name = "socknet/author_templates/remote_profile.html"
    login_url = '/login/' # For login mixin

    def get_context_data(self, **kwargs):
        context = super(ViewRemoteProfile, self).get_context_data(**kwargs)
        authorUUID = self.kwargs.get('authorUUID', self.request.user.author.uuid)
        nodeId = self.kwargs.get('nodeID')
        node = get_object_or_404(Node, id=nodeId)
        # Get the author from the other group
        url = node.url
        if url[-1] is not "/":
            url = url + "/"
        response = requests.get(url + 'author/' + authorUUID + "/", auth=HTTPBasicAuth(node.foreignNodeUser, node.foreignNodePass))
        print(response.text)

        # Ensure we got a 200
        if response.status_code is not 200:
            context['error'] = "Error: Response code was " + str(response.status_code)
            return context

        # Ensure we got data back
        if (len(response.text) < 0):
            context['error'] = "Error: No JSON was sent back."
            return context

        # Parse the json
        try:
            json_data = json.loads(response.text)
        except ValueError, error:
            context['error'] = "Error: " + str(error)
            return context

        print("\n ------------ DATA ---------------")
        print(json_data)

        serializer = ProfileSerializer(data=json_data)
        # Ensure the data is valid
        if not serializer.is_valid():
            context['error'] = "Validation Error: " + str(serializer.errors)

        author_data = serializer.validated_data
        print("\n -------------- VALIDATED DATA ---------------")
        print(author_data)

        # If the author is not in the db, create a new model
        foreign_author = None
        try:
            foreign_author = ForeignAuthor.objects.get(id=authorUUID)
        except ForeignAuthor.DoesNotExist:
            try:
                foreign_author = ForeignAuthor(id=author_data['uuid'], display_name=author_data['displayName'], node=node, url=author_data['url'])
                foreign_author.save()
            except KeyError, error:
                # This means id, display name, node, or url was missing
                context['error'] = "Key Error: " + str(error)
                return context
        context['profile_author'] = foreign_author
        context['is_friend'] = self.request.user.author.is_friend(foreign_author.id)

        """
        # Ask if the authors are friends
        response = requests.get(url + 'friends/' + authorUUID + "/" + str(self.request.user.author.uuid) + "/", auth=HTTPBasicAuth(node.foreignNodeUser, node.foreignNodePass))
        # Ensure we got a 200
        if (response.status_code is not 200) or (len(response.text) < 0):
            # If we couldn't check then display an error
            context['is_friend'] = "Error"
            return context
        else:
            try:
                json_data = json.loads(response.text)
                context['is_friend'] = json_data['friends']
            except:
                # We will error if there is no friends in the json or the json could not be parsed
                context['is_friend'] = "Error"
        """
        return context

    def check_url(self, url):
        if len(url) > 0:
            return "http://" + url
        return url

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            # Send a friend request to a remote node
            decoded_json = json.loads(request.body)
            if decoded_json['action'] == "friend_request":
                nodeId = self.kwargs.get('nodeID')
                node = get_object_or_404(Node, id=nodeId)
                authorUUID = self.kwargs.get('authorUUID', self.request.user.author.uuid)
                authorUUID = uuid.UUID(authorUUID)
                foreign_author = get_object_or_404(ForeignAuthor, id=authorUUID)
                local_author = self.request.user.author
                url = node.url
                if url[-1] is not "/":
                    url = url + "/"
                data = {
                    "query": "friendrequest",
                    "author": {
                        "id": str(local_author.uuid),
                        "host": self.check_url(local_author.host),
                        "displayName": local_author.displayName

                    },
                    "friend": {
                        "id": str(foreign_author.id),
                        "host": self.check_url(foreign_author.node.url),
                        "displayName": foreign_author.display_name,
                        "url": self.check_url(foreign_author.url)
                    }
                }
                json_data = json.dumps(data) # encode
                print(url + "friendrequest/")
                response = requests.post(url=url + "friendrequest/", headers={"content-type": "application/json"}, data=json_data, auth=HTTPBasicAuth(node.foreignNodeUser, node.foreignNodePass))
                print(response.status_code)
                print(response)
                return HttpResponse(status=200)
        # Returning 500 right now since nothing else should be posting to this page
        return HttpResponse(status=500)
