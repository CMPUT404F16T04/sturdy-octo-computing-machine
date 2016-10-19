from django.conf.urls import url
from django.contrib.auth import views as auth_view

from socknet import views

urlpatterns = [
    # Posts
    url(r'^$', views.ListPosts.as_view(), name='list_posts'),
    url(r'^post/(?P<pk>[0-9]+)/$', views.ViewPost.as_view(), name='view_post'),
    url(r'^post/create/$', views.CreatePost.as_view(), name='create_post'),

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
