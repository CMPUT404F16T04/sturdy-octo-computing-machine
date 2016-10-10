from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import html
import CommonMark
import HTMLParser

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
    
    def _unescape_markdown(self, text):
        """ Removes HTML escape characters from given text for 
        certain markdown features to work properly, which are > for blockquotes, 
        and any contents within the <code></code> tags. Then returns the result.
        
        """
        # To enable block quotes in markdown.
        tmp = text.replace('&gt;', '>')
        # Anything within <code></code> will be decoded.
        parser = HTMLParser.HTMLParser()
        # Split by the commonmark generated tags (they're not user generated).
        tmp = tmp.split('<')
        starts = 0
        ends = 0
        code_tag_contents = []
        for each in tmp:
            if each.replace(' ','').startswith('code>'):
                starts += 1
            if each.replace(' ','').startswith('/code>'):
                ends += 1
            # if currently within a <code> tag, decode html escape chars.
            if starts > ends:
                code_tag_contents.append(parser.unescape(each))
            else:
                code_tag_contents.append(each)
        return '<'.join(code_tag_contents)
    
    def get_converted_content(self):
        """ Converts and returns the instance's content appropriately whether post 
        is in markdown or in plain text. It escapes user generated content first before
        applying markdown (if applicable) and returning it.
        """
        safe_text = html.conditional_escape(self.content)
        if self.markdown:
            markdowned = self._unescape_markdown(CommonMark.commonmark(safe_text))
            return markdowned
        return safe_text
    
    def view_content(self):
        """ Retrieves content to be displayed as html, it is assumed safe 
        due to get_converted_content() upon form submitting.
        """
        return self.content
        
    # enable weird characters like lenny faces taken from:
    #http://stackoverflow.com/questions/36389723/why-is-django-using-ascii-instead-of-utf-8
    def __unicode__(self):
        return self.author.username + ": " + self.content