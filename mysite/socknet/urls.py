from django.conf.urls import url, include
from django.contrib.auth import views as auth_view
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers

from socknet.forms import CustomAuthenticationForm
from socknet.views import api_views, admin_views, author_views, post_views

urlpatterns = [
    # API

    url(r'^api/friends/(?P<authorid1>[0-9A-Fa-f-]+)/(?P<authorid2>[0-9A-Fa-f-]+)/', api_views.IsFriendQuery.as_view(), name="api_is_friend_query"),
    url(r'^api/friends/(?P<authorid>[0-9A-Fa-f-]+)/$', api_views.FriendsQuery.as_view(), name="api_friend_query"),
    url(r'^api/friendrequest/', api_views.FriendRequest.as_view(), name="api_friend_request"),

    url(r'^api/posts/(?P<post_id>[0-9A-Fa-f-]+)/$', api_views.PostIDQuery.as_view(), name="api_posts_id"),
    url(r'^api/posts/$', api_views.PostsQuery.as_view(), name="api_posts"),
    url(r'^api/author/posts', api_views.AuthorPostsViewSet.as_view(), name="api_author_posts"),
    url(r'^api/author/(?P<auth_id>[0-9A-Fa-f-]+)/posts/$', api_views.AuthorViewAllTheirPosts.as_view(), name="api_authors_posts"),
    url(r'^api/images/(?P<img>[0-9A-Fa-f-]+)$', api_views.ViewApiRawImage.as_view(), name='view_api_raw_image'),

    # Posts
    url(r'^$', post_views.ListPosts.as_view(), name='list_posts'),
    url(r'^remote_posts/$', post_views.ListRemotePosts.as_view(), name='list_remote_posts'),
    url(r'^posts/(?P<pk>[0-9A-Fa-f-]+)/$', post_views.ViewPost.as_view(), name='view_post'),
    url(r'^posts/create/$', post_views.CreatePost.as_view(), name='create_post'),
    url(r'^posts/(?P<pk>[0-9A-Fa-f-]+)/delete/$', post_views.DeletePost.as_view(), name='author_check_delete'),
    url(r'^posts/(?P<pk>[0-9A-Fa-f-]+)/update/$', post_views.UpdatePost.as_view(), name='author_check_update'),

    # Comments
    url(r'^comment/(?P<pk>[0-9A-Fa-f-]+)/$', post_views.ViewComment.as_view(), name='view_comment'),
    url(r'^posts/(?P<post_pk>[0-9A-Fa-f-]+)/comments/create/$', post_views.CreateComment.as_view(), name='create_comment'),

    # Images
    url(r'^images/(?P<img>[0-9A-Fa-f-]+)$', post_views.ViewImage.as_view(), name='view_image'),
    # Redirect static access through Authentication first.
    url(r'^media/(?P<img>[0-9A-Fa-f-]+)$', post_views.ViewRawImage.as_view(), name='view_raw_image'),

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
