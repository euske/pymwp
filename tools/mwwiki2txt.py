#!/usr/bin/env python
#
# Usage examples:
#  $ mwwiki2txt.py article12.wiki > article12.txt
#  $ mwwiki2txt.py -L article12.wiki > article12.link
#  $ mwwiki2txt.py -Z -o jawiki.txt.db jawiki.xml.bz2
#  $ mwwiki2txt.py -Z -o jawiki.txt.db jawiki.wiki.db
#  $ mwwiki2txt.py -o all.txt.bz2 jawiki.xml.bz2
#  $ mwwiki2txt.py -P 'article%(pageid)08d.txt' jawiki.xml.bz2
#
import re
import sys
from pymwp.mwtokenizer import WikiToken
from pymwp.mwtokenizer import XMLTagToken
from pymwp.mwtokenizer import XMLEmptyTagToken
from pymwp.mwparser import WikiTextParser
from pymwp.mwparser import WikiTree
from pymwp.mwparser import WikiXMLTree
from pymwp.mwparser import WikiArgTree
from pymwp.mwparser import WikiSpecialTree
from pymwp.mwparser import WikiCommentTree
from pymwp.mwparser import WikiKeywordTree
from pymwp.mwparser import WikiLinkTree
from pymwp.mwparser import WikiDivTree
from pymwp.mwparser import WikiTableTree
from pymwp.mwparser import WikiTableCellTree
from pymwp.mwparser import WikiParserError
from pymwp.mwxmldump import MWXMLDumpFilter
from pymwp.mwdb import WikiDB
from pymwp.mwdb import WikiFileWriter
from pymwp.utils import getfp


SPC = re.compile(r'\s+')
def rmsp(s): return SPC.sub(' ', s)

IGNORED = re.compile(u'^([-a-z]+|Category|Special):')
def isignored(name): return IGNORED.match(name)


##  WikiTextExtractor
##
class WikiTextExtractor(WikiTextParser):

    def __init__(self, errfp=None):
        WikiTextParser.__init__(self)
        self.errfp = errfp
        return

    def error(self, s):
        if self.errfp is not None:
            self.errfp.write(s+'\n')
        return

    def invalid_token(self, pos, token):
        self.error(f'invalid token({pos}): {token!r}')
        return

    def close(self):
        WikiTextParser.close(self)
        texts = self.convert(self.get_root())
        return u''.join(texts)

    def convert(self, tree):
        if tree is WikiToken.PAR:
            yield u'\n'
        elif isinstance(tree, XMLEmptyTagToken):
            if tree.name in XMLTagToken.BR_TAG:
                yield u'\n'
        elif isinstance(tree, str):
            yield rmsp(tree)
        elif isinstance(tree, WikiToken):
            yield rmsp(tree.name)
        elif isinstance(tree, WikiSpecialTree):
            pass
        elif isinstance(tree, WikiCommentTree):
            pass
        elif isinstance(tree, WikiXMLTree):
            if tree.xml.name in XMLTagToken.NO_TEXT:
                pass
            else:
                for c in tree:
                    for x in self.convert(c):
                        yield x
                if tree.xml.name in XMLTagToken.PAR_TAG:
                    yield u'\n'
        elif isinstance(tree, WikiKeywordTree):
            if tree:
                if isinstance(tree[0], WikiTree):
                    name = tree[0].get_text()
                else:
                    name = tree[0]
                if isinstance(name, str) and not isignored(name):
                    for x in self.convert(tree[-1]):
                        yield x
        elif isinstance(tree, WikiLinkTree):
            if 2 <= len(tree):
                for c in tree[1:]:
                    for x in self.convert(c):
                        yield x
                    yield u' '
            elif tree:
                for x in self.convert(tree[0]):
                    yield x
        elif isinstance(tree, WikiTableCellTree):
            if tree:
                for x in self.convert(tree[-1]):
                    yield x
                yield u'\n'
        elif isinstance(tree, WikiTableTree):
            for c in tree:
                if not isinstance(c, WikiArgTree):
                    for x in self.convert(c):
                        yield x
        elif isinstance(tree, WikiDivTree):
            for c in tree:
                for x in self.convert(c):
                    yield x
            yield u'\n'
        elif isinstance(tree, WikiTree):
            for c in tree:
                for x in self.convert(c):
                    yield x
        return


##  WikiLinkExtractor
##
class WikiLinkExtractor(WikiTextParser):

    def __init__(self, errfp=None):
        WikiTextParser.__init__(self)
        self.errfp = errfp
        return

    def error(self, s):
        if self.errfp is not None:
            self.errfp.write(s+'\n')
        return

    def invalid_token(self, pos, token):
        self.error(f'invalid token({pos}): {token!r}')
        return

    def close(self):
        WikiTextParser.close(self)
        texts = self.convert(self.get_root())
        return u''.join(texts)

    def convert(self, tree):
        if isinstance(tree, WikiKeywordTree):
            if tree:
                if isinstance(tree[0], WikiTree):
                    name = tree[0].get_text()
                else:
                    name = tree[0]
                if isinstance(name, str):
                    out = (u'keyword', name)
                    if 2 <= len(tree) and not isignored(name):
                        text = tree[-1].get_text()
                        out += (text,)
                    yield u'\t'.join(out)+u'\n'
        elif isinstance(tree, WikiLinkTree):
            if tree:
                if isinstance(tree[0], WikiTree):
                    url = tree[0].get_text()
                else:
                    url = tree[0]
                if isinstance(url, str):
                    out = (u'link', url)
                    if 2 <= len(tree):
                        text = tree[-1].get_text()
                        out += (text,)
                    yield u'\t'.join(out)+u'\n'
        elif isinstance(tree, WikiTree):
            for c in tree:
                for x in self.convert(c):
                    yield x
        return


##  WikiCategoryExtractor
##
class WikiCategoryExtractor(WikiTextParser):

    def __init__(self, errfp=None):
        WikiTextParser.__init__(self)
        self.errfp = errfp
        return

    def error(self, s):
        if self.errfp is not None:
            self.errfp.write(s+'\n')
        return

    def invalid_token(self, pos, token):
        self.error(f'invalid token({pos}): {token!r}')
        return

    def close(self):
        WikiTextParser.close(self)
        texts = self.convert(self.get_root())
        return u'\t'.join(texts)

    def convert(self, tree):
        if isinstance(tree, WikiKeywordTree):
            if tree:
                if isinstance(tree[0], WikiTree):
                    name = tree[0].get_text()
                else:
                    name = tree[0]
                if isinstance(name, str) and name.startswith('Category:'):
                    yield name
        elif isinstance(tree, WikiTree):
            for c in tree:
                for x in self.convert(c):
                    yield x
        return


##  MWDump2Text
##
class MWDump2Text(MWXMLDumpFilter):

    def __init__(self, converter):
        MWXMLDumpFilter.__init__(self)
        self.converter = converter
        return

    def start_page(self, pageid, title):
        MWXMLDumpFilter.start_page(self, pageid, title)
        pageid = int(pageid)
        self.converter.add_page(pageid, title)
        return

    def open_file(self, pageid, title, revid, timestamp):
        pageid = int(pageid)
        revid = int(pageid)
        return self._Stream(pageid, revid)

    def close_file(self, fp):
        self.converter.feed_text(fp.pageid, fp.revid, u''.join(fp.text))
        return

    def write_file(self, fp, text):
        fp.text.append(text)
        return

    class _Stream:
        def __init__(self, pageid, revid):
            self.pageid = pageid
            self.revid = revid
            self.text = []
            return


##  Converter
##
class Converter:

    def __init__(self, writer, klass, errfp=None):
        self.writer = writer
        self.klass = klass
        self.errfp = errfp
        return

    def close(self):
        return

    def error(self, s):
        if self.errfp is not None:
            self.errfp.write(s+'\n')
        return

    def add_page(self, pageid, title):
        print(pageid, title, file=sys.stderr)
        self.writer.add_page(pageid, title)
        return

    def feed_text(self, pageid, revid, timestamp, text):
        parser = self.klass(errfp=self.errfp)
        try:
            parser.feed_text(text)
            self.writer.add_content(pageid, revid, timestamp, parser.close())
        except WikiParserError as e:
            self.error(f'error: {e!r}')
        return

    def feed_file(self, pageid, revid, timestamp, fp):
        parser = self.klass(errfp=self.errfp)
        try:
            parser.feed_file(fp)
            self.writer.add_content(pageid, revid, timestamp, parser.close())
        except WikiParserError as e:
            self.error(f'error: {e!r}')
        return

# main
def main(argv):
    import getopt
    def usage():
        print (f'usage: {argv[0]} [-L|-C] [-d] [-o output]'
               ' [-P pathpat] [-c encoding] [-T] [-Z] [file ...]')
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'LCdo:P:c:m:TZ')
    except getopt.GetoptError:
        return usage()
    args = args or ['-']
    errfp = None
    output = '-'
    encoding = 'utf-8'
    pathpat = None
    mode = 'page'
    titleline = False
    gzipped = False
    klass = WikiTextExtractor
    for (k, v) in opts:
        if k == '-d': errfp = sys.stderr
        elif k == '-o': output = v
        elif k == '-P': pathpat = v
        elif k == '-c': encoding = v
        elif k == '-m': mode = v
        elif k == '-T': titleline = True
        elif k == '-Z': gzipped = True
        elif k == '-L': klass = WikiLinkExtractor
        elif k == '-C': klass = WikiCategoryExtractor
    if output.endswith('.db'):
        writer = WikiDB(output, gzipped=gzipped)
    else:
        writer = WikiFileWriter(
            output=output, pathpat=pathpat,
            encoding=encoding, titleline=titleline, mode=mode)
    try:
        converter = Converter(writer, klass, errfp=errfp)
        for path in args:
            if path.endswith('.db'):
                reader = WikiDB(path, gzipped=gzipped)
                for (pageid,title) in reader:
                    revids = reader[pageid]
                    converter.add_page(pageid, title)
                    for (revid,timestamp) in revids:
                        data = reader.get_content(revid)
                        converter.feed_text(pageid, revid, timestamp, data)
            else:
                (path,fp) = getfp(path, encoding=encoding)
                if path.endswith('.xml'):
                    parser = MWDump2Text(converter)
                    parser.feed_file(fp)
                    parser.close()
                else:
                    converter.add_page(0, path)
                    converter.feed_file(0, 0, '', fp)
                fp.close()
        converter.close()
    finally:
        writer.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
