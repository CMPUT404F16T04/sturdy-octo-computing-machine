from django.conf.urls import url
from django.contrib.auth import views as auth_view

from socknet import views

urlpatterns = [
    url(r'^$', views.ListPosts.as_view(), name='list_posts'),
    url(r'^post/(?P<pk>[0-9]+)/$', views.ViewPost.as_view(), name='view_post'),
    url(r'^post/create/$', views.CreatePost.as_view(), name='create_post'),
    url(r'^login/$', auth_view.login, name='login'),
    url(r'^logged_out/$', auth_view.logout, name='logged_out'),
]
