from django.conf.urls import url, include
from django.contrib.auth import views as auth_view
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers

from socknet.forms import CustomAuthenticationForm
from socknet.views import api_views, admin_views, author_views, post_views

# API Routes
router = routers.DefaultRouter()

# http://service/author/posts (posts that are visible to the currently authenticated user)
router.register(r'author/posts', api_views.AuthorPostsViewSet)
# http://service/posts (all posts marked as public on the server)
# http://service/posts/{POST_ID} access to a single post with id = {POST_ID}
router.register(r'posts', api_views.PostsViewSet)
# http://service/author/{AUTHOR_ID}/posts (all posts made by {AUTHOR_ID} visible to the currently authenticated user)
router.register(r'author', api_views.AuthorViewSet)
# http://service/posts/{post_id}/comments access to the comments in a post
# TODO
# router.register(r'', views.)

urlpatterns = [
    # API
    url(r'^api/', include(router.urls)),
    url(r'^api/posts/(?P<pk>[0-9A-Fa-f-]+)/comments/$', api_views.CommentsViewSet, name="api_get_comments"),
    url(r'^api/friends/(?P<authorid1>[0-9A-Fa-f-]+)/(?P<authorid2>[0-9A-Fa-f-]+)/$', api_views.IsFriendQuery.as_view(), name="api_is_friend_query"),
    url(r'^api/friends/(?P<authorid>[0-9A-Fa-f-]+)/$', api_views.FriendsQuery.as_view(), name="api_friend_query"),
    url(r'^api/friendrequest/$', api_views.FriendRequest.as_view(), name="api_friend_request"),

    # Posts
    url(r'^$', post_views.ListPosts.as_view(), name='list_posts'),
    url(r'^posts/(?P<pk>[0-9A-Fa-f-]+)/$', post_views.ViewPost.as_view(), name='view_post'),
    url(r'^posts/create/$', post_views.CreatePost.as_view(), name='create_post'),
    url(r'^posts/(?P<pk>[0-9A-Fa-f-]+)/delete/$', post_views.DeletePost.as_view(), name='author_check_delete'),
    url(r'^posts/(?P<pk>[0-9A-Fa-f-]+)/update/$', post_views.UpdatePost.as_view(), name='author_check_update'),

    # Comments
    url(r'^comment/(?P<pk>[0-9A-Fa-f-]+)/$', post_views.ViewComment.as_view(), name='view_comment'),
    url(r'^posts/(?P<post_pk>[0-9A-Fa-f-]+)/comments/create/$', post_views.CreateComment.as_view(), name='create_comment'),

    # Images
    url(r'^images/(?P<img>[0-9A-Za-z-_./\\]+)$', post_views.ViewImage.as_view(), name='view_image'),
    # Redirect static access through Authentication first.
    url(r'^media/(?P<img>[0-9A-Za-z-_./\\]+)$', post_views.ViewRawImage.as_view(), name='view_raw_image'),

    # Profile
    url(r'^profile/(?P<authorUUID>[0-9A-Fa-f-]+)/$', author_views.ViewProfile.as_view(), name='profile'),
    url(r'^edit_profile/(?P<authorUUID>[0-9A-Fa-f-]+)/$', author_views.EditProfile.as_view(), name='editprofile'),

    # Friend Management
    url(r'^friends/(?P<authorUUID>[0-9A-Fa-f-]+)/$', author_views.ManageFriends.as_view(), name='manage_friends'),
    url(r'^following/(?P<authorUUID>[0-9A-Fa-f-]+)/$', author_views.ManageFollowing.as_view(), name='manage_following'),
    url(r'^friend_requests/(?P<authorUUID>[0-9A-Fa-f-]+)/$', author_views.ManageFriendRequests.as_view(), name='manage_friend_requests'),

    #  Authentication
    url(r'^login/$', auth_view.login, {'authentication_form': CustomAuthenticationForm}, name='login'),
    url(r'^logout/$', auth_view.logout, {'next_page': '/login/'}, name='logout'),
    url(r'^register/$', admin_views.RegistrationView.as_view(), name='registration'),
] + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# ^ static() This helper function works only in debug mode, and only if the given prefix is local and not an URL.
# https://docs.djangoproject.com/en/1.10/howto/static-files/#serving-uploaded-files-in-development
