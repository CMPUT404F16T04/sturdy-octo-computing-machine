from django.conf.urls import url
from django.contrib.auth import views as auth_view

from socknet import views

urlpatterns = [
    # Posts
    url(r'^$', views.ListPosts.as_view(), name='list_posts'),
    url(r'^posts/(?P<pk>[0-9]+)/$', views.ViewPost.as_view(), name='view_post'),
    url(r'^posts/create/$', views.CreatePost.as_view(), name='create_post'),
    url(r'^posts/(?P<pk>[0-9]+)/delete$', views.DeletePost.as_view(), name='author_check_delete'),

    # Comments
    url(r'^posts/(?P<post_pk>[0-9]+)/comments/$', views.ListComments.as_view(), name='list_comments'),
    url(r'^posts/(?P<post_pk>[0-9]+)/comments/\#(?P<pk>[0-9]+)$', views.ListComments.as_view(), name='list_comments_anchor'),
    url(r'^comment/(?P<pk>[0-9]+)/$', views.ViewComment.as_view(), name='view_comment'),
    url(r'^posts/(?P<post_pk>[0-9]+)/comments/create/$', views.CreateComment.as_view(), name='create_comment'),

    # Profile
    url(r'^profile/(?P<authorUUID>[0-9A-Fa-f-]+)/$', views.ViewProfile.as_view(), name='profile'),

    # Friend Management
    url(r'^friends/(?P<authorUUID>[0-9A-Fa-f-]+)/$', views.ManageFriends.as_view(), name='manage_friends'),
    url(r'^following/(?P<authorUUID>[0-9A-Fa-f-]+)/$', views.ManageFollowing.as_view(), name='manage_following'),
    url(r'^friend_requests/(?P<authorUUID>[0-9A-Fa-f-]+)/$', views.ManageFriendRequests.as_view(), name='manage_friend_requests'),

    #  Authentication
    url(r'^login/$', auth_view.login, name='login'),
    url(r'^logged_out/$', auth_view.logout, name='logged_out'),
]
