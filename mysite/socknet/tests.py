#!/usr/bin/python
# -*- coding: utf-8 -*-
# Taken from https://www.python.org/dev/peps/pep-0263/
# Taken from https://www.python.org/dev/peps/pep-0414/
from __future__ import unicode_literals
from django.test import TestCase
from socknet.models import Post

# Create your tests here.
class PostsTests(TestCase):

    def test_is_plaintext_safe(self):
        """ Test if plaintext is safe: converts < > to &lt; &gt; etc.
        Additionally ignores \n it does not convert that to <br/>
        because the templates which use "linebreaksbr" already take care of that.
        """
        test_content = '#testing<b>\nno'
        test_expect = '#testing&lt;b&gt;<br/>no'
        model = Post()
        model.content = test_content
        model.markdown = False
        model.content = model.get_converted_content()
        self.assertEqual(model.view_content(), test_expect)
        
    def test_is_markdown(self):
        """ Tests markdown if it works, i.e. changes # to <h1> and still ignores 
        the \n since not needed due to html template's "linebreaksbr"
        """
        test_content = '# testing\n<b>\n>test-block'
        test_expect = '<h1>testing</h1><br/><p>&lt;b&gt;</p><br/><blockquote><br/><p>test-block</p><br/></blockquote><br/>'
        model = Post()
        model.content = test_content
        model.markdown = True
        model.content = model.get_converted_content()
        self.assertEqual(model.view_content(), test_expect)
        
    def test_accepts_weird_characters(self):
        lennyeh = unicode("( ͡° ͜ʖ ͡°) \n¯\_ツ_/¯")
        lenny_result = unicode("( ͡° ͜ʖ ͡°) <br/>¯\_ツ_/¯")
        model = Post()
        model.content = lennyeh
        model.markdown = False
        model.content = model.get_converted_content()
        self.assertEqual(model.view_content(), lenny_result)
        