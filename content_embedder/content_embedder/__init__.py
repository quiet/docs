import markdown
import os
import re
import io


class ContentEmbedderPattern(markdown.inlinepatterns.Pattern):
    def __init__ (self, md, docs_dir=None):
        markdown.inlinepatterns.Pattern.__init__(self, r'{{(.*)}}')
        self.md = md
        self.docs_dir = docs_dir

    def handleMatch(self, m):
        filename = m.group(2).strip()
        input_path = os.path.join(self.docs_dir, filename)

        try:
            input_content = io.open(input_path, 'r', encoding='utf-8').read()
        except IOError:
            return ''

        t = markdown.util.etree.fromstring('<div>' + self.md.convert(input_content) + '</div>')
        return t


class ContentEmbedderExtension(markdown.Extension):
    def __init__(self, *args, **kwargs):
        self.docs_dir = kwargs.pop('docs_dir', 'docs_dir')
        super(ContentEmbedderExtension, self).__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns['content_embedder'] = ContentEmbedderPattern(md, docs_dir=self.docs_dir)


def makeExtension(**configs):
    return ContentEmbedderExtension(**configs)
