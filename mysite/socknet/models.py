from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
import CommonMark

class Post(models.Model):
    """ Represents a post made by a user """
    author = models.ForeignKey(User)
    content = models.TextField(max_length=512)
    created_on = models.DateTimeField(auto_now=True)
    markdown = models.BooleanField()

    def get_absolute_url(self):
        """ Gets the canonical URL for a Post
        Will be of the format .../post/<id>/
        """
        return reverse('view_post', args=[str(self.id)])

    def view_content(self):
        if(self.markdown):
            return CommonMark.commonmark(self.content)
        return self.content.replace("\n", "<br/>")
        
    # enable weird characters like lenny faces taken from:
    #http://stackoverflow.com/questions/36389723/why-is-django-using-ascii-instead-of-utf-8
    def __unicode__(self):
        return self.author.username + ": " + self.content