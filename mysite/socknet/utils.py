from django.utils import html
import CommonMark
import HTMLParser


class HTMLsafe():
    """ Makes text html safe and can apply markdown """
    @staticmethod
    def _unescape_markdown(text):
        """ Removes HTML escape characters from given text for <code> tags
        in markdown to work properly: any contents within the <code></code> tags
        gets decoded. Then returns the result.

        """
        tmp = text
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

    @staticmethod
    def get_converted_content(markdown, text):
        """ Converts and returns the instance's content appropriately whether post
        is in markdown or in plain text. It escapes user generated content first before
        applying markdown (if applicable) and returning it.
        """
        safe_text = html.conditional_escape(text)
        if markdown:
            # To enable block quotes in markdown.
            mark = safe_text.replace('&gt;', '>')
            mark = CommonMark.commonmark(mark)
            markdowned = HTMLsafe._unescape_markdown(mark)
            return markdowned.replace('\n', '<br/>')
        return safe_text.replace('\n', '<br/>')