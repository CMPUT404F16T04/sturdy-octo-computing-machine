import uuid
import json
import datetime
import urllib
from django.shortcuts import get_object_or_404, redirect
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, FileResponse
from django.views.generic.edit import DeleteView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from socknet.models import *
from socknet.forms import *
from socknet.serializers import *
from socknet.utils import *


# For images
import os
from mysite.settings import MEDIA_ROOT
from PIL import Image, ImageFile
import base64

import requests
from requests.auth import HTTPBasicAuth


class ListPosts(LoginRequiredMixin, UserPassesTestMixin, generic.ListView):
    """ Displays a list of all posts in the system """
    queryset = Post.objects.filter(visibility='PUBLIC').order_by('-created_on')
    template_name = 'socknet/post_templates/list_posts.html'
    login_url = '/login/' # For login mixin
    context_object_name = 'posts_list'
    paginate_by = 10

    def test_func(self):
        try:
            self.request.user.author
        except:
            return False
        else:
            return True

class ListRemotePosts(LoginRequiredMixin, UserPassesTestMixin, generic.ListView):
    """ Displays a list of all posts in the system """
    template_name = 'socknet/post_templates/list_remote_posts.html'
    login_url = '/login/' # For login mixin
    context_object_name = 'posts_list'

    def get_queryset(self):
        posts = []
        for n in Node.objects.all():
            print "\nFetching Post Lists data from Node: " + n.name
            url = n.url
            # In case entered like host.com/api instead of host.com/api/
            url = HTMLsafe.get_url_fixed(n.url)
            # In case entered like host.com/api instead of host.com/api/
            print url
            r = requests.get(url + 'posts', auth=HTTPBasicAuth(n.foreignNodeUser, n.foreignNodePass))

            if r.status_code is not 200:
                print("Error response code was bad: " + str(r.status_code) + " from: " + n.name)
            elif (len(r.text) < 1):
                print("Response was empty from: " + n.name)
            else:
                data = {}
                try:
                    # Parse the json
                    data = json.loads(r.text)
                    try:
                        for post_json in data['posts']:
                            serializer = PostsSerializer(data=post_json)
                            valid = serializer.is_valid()
                            if not valid:
                                # Ignore posts that are not valid
                                print("Error from group: " + n.name + ", serializer is not valid.")
                                print(serializer.errors)
                            else:
                                post_data = serializer.validated_data
                                post_author = post_data['author']

                                post = RemotePost(post_json['id'], post_data['title'], post_data['description'], post_data['contentType'],
                                    post_data['content'], post_data['visibility'], post_data['published'], post_author['displayName'], post_author['id'],n)
                                posts.append(post)
                    except Exception as e:
                        print("Error from group: " + n.name + "while parsing post data")
                        print(str(e))
                except Exception as e:
                    print("Error from group: " + n.name + "after calling json.loads:")
                    print(str(e))
        if len(posts) > 0:
            return sorted(posts, reverse=True, key=lambda RemotePost: RemotePost.published)
        return posts

    def test_func(self):
        try:
            self.request.user.author
        except:
            return False
        else:
            return True

class ListFriendsPosts(LoginRequiredMixin, UserPassesTestMixin, generic.ListView):
    template_name = 'socknet/post_templates/friends_posts.html'
    login_url = '/login/' # For login mixin
    context_object_name = 'posts_list'

    def get_queryset(self):
        posts_list = []
        author = self.request.user.author

        # Get all of the authors friends
        local_friends = author.friends.all()
        remote_friends = author.foreign_friends.all()

        if len(local_friends) > 0:
            for friend in local_friends:
                # We want posts marked PUBLIC, FRIENDS, FOAF, SERVERONLY
                # Since we are their friend, we should be allowed to see FOAF posts
                local_posts = Post.objects.filter(author=friend).exclude(visibility="PRIVATE")
                # Convert posts to PostDetail object
                for post in local_posts:
                    posts_list.append(PostDetails(post, True))

        if len(remote_friends) > 0:
            for friend in remote_friends:
                print("Attempting to get posts from " + friend.display_name + " from " + friend.node.name)
                # Get our friends posts
                url = friend.node.url
                if url[-1] is not "/":
                    url = url + "/"
                # Send the request to the other server
                url = url + "author/" + str(friend.id) + "/posts"
                print(url)
                response = None
                try:
                    response = requests.get(url=url, auth=HTTPBasicAuth(friend.node.foreignNodeUser, friend.node.foreignNodePass), timeout=5) # TIME OUT AFTER 5 SEC
                    # Ensure we got a 200
                except requests.exceptions.Timeout as e:
                    print("The request timed out for " + friend.display_name + " from " + friend.node.name)

                if response.status_code is not 200:
                    error = "Error: Response code was " + str(response.status_code) + " for " + friend.display_name + " from " + friend.node.name
                    print error
                # Ensure we got data back
                elif (len(response.text) < 0):
                    error = "Error: No JSON was sent back for " + friend.display_name + " from " + friend.node.name
                    print error
                else:
                    # At this point, we got a 200 and some data
                    try:
                        data = json.loads(response.text)
                        # Loop through the posts
                        for post_json in data['posts']:
                            serializer = PostsSerializer(data=post_json)
                            if not serializer.is_valid():
                                print("Error: Post is not valid from " + friend.display_name + " from " + friend.node.name + " reason:")
                                print(serializer.errors)
                            else:
                                post_uuid = uuid.UUID(post_json['id']) # If uuid is not valid, an error will be thrown
                                # If the post json is valid, create a post details object.
                                # Note: PostDetails will throw a key error if an essiential item is missing, such as title or content
                                post = PostDetails(serializer.validated_data, False, friend.node, post_uuid)
                                # Only display the post if it is PUBLIC, FOAF, or FRIENDS
                                if post.visibility == "PUBLIC" or post.visibility == "FOAF" or post.visibility == "FRIENDS":
                                    posts_list.append(post)
                    except Exception as e:
                        error = "Error: " + str(e) + " for " + friend.display_name + " from " + friend.node.name
                        print error

        if len(posts_list) > 0:
            return sorted(posts_list, reverse=True, key=lambda PostDetails: PostDetails.published)
        return posts_list

    def test_func(self):
        try:
            self.request.user.author
        except:
            return False
        else:
            return True

class ViewPost(LoginRequiredMixin, generic.detail.DetailView):
    """ Displays the details of a single post """
    model = Post
    template_name = 'socknet/post_templates/view_post.html'
    login_url = '/login/' # For login mixin

    def get_context_data(self, **kwargs):
        context = super(ViewPost, self).get_context_data(**kwargs)
        page = self.request.GET.get('page')

        comments = []
        foreign_comments = ForeignComment.objects.filter(parent_post_id=context['post'].id)
        for comment in foreign_comments:
            comments.append(CommentDetails(comment, False))

        local_comments = Comment.objects.all_comments_for_post(context['post'].id, True)
        for comment in local_comments:
            comments.append(CommentDetails(comment, True))

        context['num_comments'] = len(comments)
        context['comments'] = comments
        paginator = Paginator(comments, 5)

        try:
            comments = paginator.page(page)
        except PageNotAnInteger:
            comments = paginator.page(1)
        except EmptyPage:
            comments = paginator.page(paginator.num_pages)
        return context

class ViewRemotePost(LoginRequiredMixin, generic.base.TemplateView):
    """ Displays the details of a remote foreign post """
    template_name = 'socknet/post_templates/view_remote_post.html'
    login_url = '/login/' # For login mixin

    def get_context_data(self, **kwargs):
        context = super(ViewRemotePost, self).get_context_data(**kwargs)
        n = get_object_or_404(Node, id=self.kwargs['nodeID'])
        pid = self.kwargs['pk']
        comments = []
        post_original = None

        print "Fetching Post & Comment data from Node: " + n.name
        url = HTMLsafe.get_url_fixed(n.url)
        # In case entered like host.com/api instead of host.com/api/
        print "API URL: " + url
        rpost = requests.get(url + 'posts/' + str(pid), auth=HTTPBasicAuth(n.foreignNodeUser, n.foreignNodePass))
        r = requests.get(url + 'posts/' + str(pid) + "/comments", auth=HTTPBasicAuth(n.foreignNodeUser, n.foreignNodePass))
        print "Response received"
        print "comments status code:" + str(r.status_code)
        print "post status code:" + str(rpost.status_code)
        #print rpost.text
        #print r.text

        # Ensure we got a 200
        if r.status_code is not 200:
            err = "Error: Response code of url/posts/{id}/comments was " + str(r.status_code)
            context['error'] = err
            print err
        if rpost.status_code is not 200:
            err = "Error: Response code of url/posts/{id} was " + str(r.status_code)
            context['error'] = err
            print err
        # Ensure we got data back
        if (len(r.text) < 0):
            err = "Error: No JSON from url/posts/{id}/comments was sent back."
            context['error'] = err
            print err
        if (len(rpost.text) < 0):
            err = "Error: No JSON from url/posts/{id} was sent back."
            context['error'] = err
            print err

        datafind = {}
        postfind = None
        try:
            postfind = json.loads(rpost.text)
            datafind = json.loads(r.text)
        except ValueError, error:
            context['error'] = "Error: " + str(error)
            print("ValueError json loads in post_views.py ViewRemotePost" + str(error))
        try:
            if postfind is not None :
                postdat = postfind['posts']
                print(postdat)
                post_original = RemotePost(postdat['id'], postdat['title'], postdat['description'], postdat['contentType'],
                            postdat['content'], postdat['visibility'], postdat['published'], postdat['author']['displayName'], postdat['author']['id'],n)
            for i in datafind['comments']:
                # at utils.py RemoteComment((self, guid, content_type, content, pubdate, author_display_name, author_id, auth_host, node)
                dat = RemoteComment(i['guid'], i['contentType'], i['comment'], i['pubDate'], i['author']['displayName'], i['author']['id'], i['author']['host'], n.url)
                comments.append(dat)
        except KeyError, error:
            context['error'] = "Error: comments KeyError, " + str(error)
            print("KeyError json loads for comments in post_views.py ViewRemotePost" + str(error))

        try:
            context['post_auth_id'] = post_original.author_id
        except AttributeError, error:
            context['post_auth_id'] = None
        context['postdat'] = post_original
        context['num_comments'] = len(comments)
        context['comments_list'] = comments
        return context

    def test_func(self):
        try:
            self.request.user.author
        except:
            return False
        else:
            return True

class CreatePost(LoginRequiredMixin, generic.edit.CreateView):
    """ Displays a form for creating a new post """
    model = Post
    template_name = 'socknet/post_templates/create_post.html'
    fields = ['title', 'description','content', 'markdown', 'visibility']
    login_url = '/login/' # For login mixin

    def form_valid(self, form):
        # Create the post object first.
        form.instance.author = self.request.user.author
        http_res_obj = super(CreatePost, self).form_valid(form)
        # If there was an image, make image object
        # https://docs.djangoproject.com/en/1.10/ref/request-response/#django.http.HttpRequest
        if not self.request.FILES == {}:
            try:
                # taken from Dtephen Paulger http://stackoverflow.com/a/20762344
                Image.open(self.request.FILES['image']).verify()
            except IOError:
                response = HttpResponse(status=415)
                response.write("<center><h1>415 Unsupported Media Type</h1><br/>Please make sure the file is an image.\
                    <br/><h2><a onclick=\"window.history.back()\" href=\"#\">Go Back</a></h2></center>")
                # Don't save this post entry, because faulty image.
                form.instance.delete()
                return response
            upload_obj = self.request.FILES['image']
            # Seek 0,0 because for some reason it is not set to the beginning of the file...
            # This caused a lot of trouble... why isn't it automatically set to begginning of file ?!
            upload_obj.seek(0, 0)
            image_dat = upload_obj.read()
            imagetype = upload_obj.content_type
            img = ImageServ.objects.create_image(image_dat, self.request.user.author, form.instance, imagetype)
            # Update field of the created post with the image path.
            form.instance.imglink = img.id
            link_str = "http://" + self.request.get_host() + "/media/" + str(img.id)
            # If post already close to 512 max char, link may be cut or even not be there...
            if form.instance.markdown:
                form.instance.content = form.instance.content + "\n![Attached Image](" + link_str + ")"
            else:
                form.instance.content = form.instance.content + "\nLinked image: " + link_str
            form.instance.save(update_fields=['imglink'])
            form.instance.save(update_fields=['content'])
        return http_res_obj

class DeletePost(LoginRequiredMixin, generic.edit.DeleteView):
    """ Displays a form for deleting posts  """
    model = Post
    template_name = 'socknet/post_templates/author_check_delete.html'
    login_url = '/login/' # For login mixin
    success_url=('/')

    def get_context_data(self, **kwargs):
        context = super(DeletePost, self).get_context_data(**kwargs)
        context['deny'] = ForbiddenContent403.deniedhtml();
        return context

    def form_valid(self, form):
        return super(DeletePost, self).form_valid(form)

class UpdatePost(LoginRequiredMixin, generic.edit.UpdateView):
    """ Displays a form for editing posts  """
    model = Post
    template_name = 'socknet/post_templates/author_check_update.html'
    login_url = '/login/' # For login mixin
    success_url = '/'
    fields = ('title', 'description', 'content', 'markdown', 'visibility')

    def get_context_data(self, **kwargs):
        context = super(UpdatePost, self).get_context_data(**kwargs)
        context['deny'] = ForbiddenContent403.deniedhtml();
        return context

    def get_object(self, queryset=None):
        obj = Post.objects.get(id=self.kwargs['pk'])
        return obj

class ViewComment(LoginRequiredMixin, generic.base.TemplateView):
    """ Displays a specific comment for the post
    """
    model = Comment
    template_name = 'socknet/post_templates/comment.html'
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
    template_name = 'socknet/post_templates/create_comment.html'
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

class CreateForeignComment(LoginRequiredMixin, generic.base.TemplateView):
    """ Displays a form for creating a new foreign comment """
    template_name = 'socknet/post_templates/create_foreign_comment.html'
    fields = ['content', 'markdown']
    login_url = '/login/' # For login mixin

    def get_context_data(self, **kwargs):
        context = super(CreateForeignComment, self).get_context_data(**kwargs)
        pid = self.kwargs.get('pk')
        node_obj = Node.objects.get(id=self.kwargs.get('nodeID'))
        # POST to http://service/posts/{POST_ID}/comments
        make_comment_url = HTMLsafe.get_url_fixed(node_obj.url) + "posts/" + pid + "/comments"
        context['foreign_pid'] = pid
        context['foreign_node'] = node_obj
        context['create_comment_api'] = make_comment_url
        return context

    def post(self, request, *args, **kwargs):
        bdy = request.body
        auth = self.request.user.author
        ls = bdy.split("&")
        params = {}
        for each in ls:
            v = each.split("=")
            params[v[0]] = v[1]

        markdown = "text/plain"
        if params.get(markdown,"off").lower() == "on":
            markdown = "text/x-markdown"

        node_obj = Node.objects.get(id=self.kwargs.get('nodeID'))

        cmt = {
            "author":{
               # ID of the Author (UUID)
               "id": str(auth.uuid),
               "host": "https://" + str(request.get_host()) + "/api",
               "displayName": str(auth.displayName),
               # url to the authors information
               "url": request.get_host() + "/author/" + str(auth.uuid),
               # HATEOS url for Github API
               "github": str(auth.github_url)
            },
            "comment": urllib.unquote_plus(params['comment']),
            "contentType": markdown,
            # ISO 8601 TIMESTAMP
            "published": str(datetime.datetime.utcnow().isoformat()) + "Z",
            # ID of the Comment (UUID)
            "guid": str(uuid.uuid4())
        }
        url_str = str(HTMLsafe.get_url_fixed(node_obj.url))
        url_post = url_str + "posts/" + self.kwargs.get('pk')
        add = {
            "query" : "addComment",
            "post" : str(url_post),
            "comment" : cmt
            }
        head = {
            "content-type" : "application/json"
        }
        req = requests.post(url_post + '/comments/', auth=HTTPBasicAuth(node_obj.foreignNodeUser, node_obj.foreignNodePass), data=json.dumps(add), headers=head)
        #print add
        print "\n\n-----------------CREATING A FOREIGN COMMENT"
        print "Received status code:" + str(req.status_code)
        print req.text
        print "WHAT WE SEND YOU"
        print  json.dumps(add)
        print "----------------END"
        #print str(req.text)
        # content_type="application/json"
        #nodeID>[0-9]+)/remote_posts/(?P<pk
        r = HttpResponse(status=200)
        r.write(url_post + "<br>" + str(add) + "<br> received status code: " + str(req.status_code) + "<br>" + str(req.text))
        #return r
        return redirect("view_remote_post", nodeID = node_obj.id, pk = self.kwargs.get('pk'))

class ViewImage(LoginRequiredMixin, generic.base.TemplateView):
    """ Get the normal image view. """
    model= ImageServ
    template_name = "socknet/post_templates/image.html"
    login_url = '/login/' # For login mixin
    def get_context_data(self, **kwargs):
        context = super(ViewImage, self).get_context_data(**kwargs)
        parent_key = self.kwargs.get('img')
        imgobj = ImageServ.objects.get(pk=parent_key)
        context['image_usr'] = imgobj.author.displayName
        context['image_made'] = imgobj.created_on
        context['image_id'] = imgobj.id
        context['b64'] = "data:" + imgobj.imagetype + ";base64," +  base64.b64encode(imgobj.image)
        return context

"""
No authentication, it opens image as blob and then
encode it to base64 and put that in the html.
"""
def raw_image_serve(request, img):
    imgobj = ImageServ.objects.get(pk=img)
    imgdat = imgobj.image
    #return FileResponse(imgobj.image)
    r = HttpResponse()
    r["Content-Type"] = imgobj.imagetype
    r["Content-Length"] = len(imgdat)
    r.write(imgdat)
    return r
