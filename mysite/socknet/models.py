from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User

class Post(models.Model):
    """ Represents a post made by a user """
    author = models.ForeignKey(User)
    content = models.TextField(max_length=512)
    created_on = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        """ Gets the canonical URL for a Post
        Will be of the format .../post/<id>/
        """
        return reverse('view_post', args=[str(self.id)])

    def view_content(self):
        #return self.content.replace("\n","<br>")
        return self.content.split("\n")
        
    def __str__(self):
        return self.author.username + ": " + self.content
