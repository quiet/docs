import markdown
import os
import re
import io


class ContentEmbedderPattern(markdown.inlinepatterns.Pattern):
    def __init__ (self, md, docs_dir=None):
        markdown.inlinepatterns.Pattern.__init__(self, r'{{(.*)}}')
        self.md = md
        self.docs_dir = docs_dir
        self.blocks = []

    def handleMatch(self, m):
        filename = m.group(1).strip()
        input_path = os.path.join(self.docs_dir, filename)

        try:
            input_content = io.open(input_path, 'r', encoding='utf-8').readlines()
        except IOError:
            try:
                os.makedirs(os.path.dirname(input_path))
            except OSError:
                pass
            with open(input_path, 'w') as f:
                pass
            return []

        return input_content

    embedder_re = re.compile(r'{{(.*)}}')
    def run(self, lines):
        new_lines = []
        for line in lines:
            m = self.embedder_re.match(line)
            if m:
                new_lines.extend(self.handleMatch(m))
            else:
                new_lines.append(line)

        return new_lines


class ContentEmbedderExtension(markdown.Extension):
    def __init__(self, *args, **kwargs):
        self.docs_dir = kwargs.pop('docs_dir', 'docs')
        super(ContentEmbedderExtension, self).__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        inst = ContentEmbedderPattern(md, docs_dir=self.docs_dir)
        md.preprocessors.add('content_embedder', inst, '_begin')
        # md.postprocessors.add('content_embedder', inst, '_begin')


def makeExtension(**configs):
    return ContentEmbedderExtension(**configs)
