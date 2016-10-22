from django.conf.urls import url
from django.contrib.auth import views as auth_view
from django.conf import settings
from django.conf.urls.static import static
from socknet import views

urlpatterns = [
    # Posts
    url(r'^$', views.ListPosts.as_view(), name='list_posts'),
    url(r'^posts/(?P<pk>[0-9A-Fa-f-]+)/$', views.ViewPost.as_view(), name='view_post'),
    url(r'^posts/create/$', views.CreatePost.as_view(), name='create_post'),
    url(r'^posts/(?P<pk>[0-9A-Fa-f-]+)/delete/$', views.DeletePost.as_view(), name='author_check_delete'),

    # Comments
    url(r'^posts/(?P<post_pk>[0-9A-Fa-f-]+)/comments/$', views.ListComments.as_view(), name='list_comments'),
    url(r'^posts/(?P<post_pk>[0-9A-Fa-f-]+)/comments/\#(?P<pk>[0-9A-Fa-f-]+)$', views.ListComments.as_view(), name='list_comments_anchor'),
    url(r'^comment/(?P<pk>[0-9A-Fa-f-]+)/$', views.ViewComment.as_view(), name='view_comment'),
    url(r'^posts/(?P<post_pk>[0-9A-Fa-f-]+)/comments/create/$', views.CreateComment.as_view(), name='create_comment'),

    # Images
    url(r'^images/upload$', views.UploadImage.as_view(), name='upload_image'),
    url(r'^images/(?P<img>[0-9A-Za-z-_./\\]+)$', views.ViewImage.as_view(), name='view_image'),
    
    # Profile
    url(r'^profile/(?P<authorUUID>[0-9A-Fa-f-]+)/$', views.ViewProfile.as_view(), name='profile'),

    # Friend Management
    url(r'^friends/(?P<authorUUID>[0-9A-Fa-f-]+)/$', views.ManageFriends.as_view(), name='manage_friends'),
    url(r'^following/(?P<authorUUID>[0-9A-Fa-f-]+)/$', views.ManageFollowing.as_view(), name='manage_following'),
    url(r'^friend_requests/(?P<authorUUID>[0-9A-Fa-f-]+)/$', views.ManageFriendRequests.as_view(), name='manage_friend_requests'),

    #  Authentication
    url(r'^login/$', auth_view.login, name='login'),
    url(r'^logged_out/$', auth_view.logout, name='logged_out'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# ^ static() This helper function works only in debug mode, and only if the given prefix is local and not an URL.
# https://docs.djangoproject.com/en/1.10/howto/static-files/#serving-uploaded-files-in-development
