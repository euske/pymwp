#!/usr/bin/env python2
#
# usage:
#  $ mwwiki2txt.py -n10 -t 'article%(pageid)05d.txt' jawiki.xml.bz2
#
import re
import sys
from gzip import GzipFile
from bz2 import BZ2File
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from pymwp.mwtokenizer import WikiToken, XMLTagToken, XMLEmptyTagToken
from pymwp.mwparser import WikiTextParser
from pymwp.mwparser import WikiTree, WikiXMLTree, WikiArgTree
from pymwp.mwparser import WikiSpecialTree, WikiCommentTree
from pymwp.mwparser import WikiKeywordTree, WikiLinkTree
from pymwp.mwparser import WikiDivTree
from pymwp.mwparser import WikiTableTree, WikiTableCellTree
from pymwp.mwxmldump import MWXMLDumpFilter
from pymwp.pycdb import CDBReader, CDBMaker


SPC = re.compile(r'\s+')
def rmsp(s): return SPC.sub(' ', s)

IGNORED = re.compile(u'^([-a-z]+|Category|Special):')
def isignored(name): return IGNORED.match(name)


##  WikiTextExtractor
##
class WikiTextExtractor(WikiTextParser):

    def __init__(self, outfp, errfp=sys.stderr, codec='utf-8'):
        WikiTextParser.__init__(self)
        self.outfp = outfp
        self.errfp = errfp
        self.codec = codec
        return

    def close(self):
        self.convert(self.outfp)
        WikiTextParser.close(self)
        return

    def error(self, s):
        self.errfp.write(s)
        return

    def invalid_token(self, pos, token):
        if self.errfp is not None:
            self.error('invalid token(%d): %r\n' % (pos, token))
        return

    def convert(self, fp):
        stack = [self.get_root()]
        while stack:
            tree = stack.pop()
            if isinstance(tree, str):
                fp.write(tree)
            elif tree is WikiToken.PAR:
                fp.write('\n')
            elif isinstance(tree, XMLEmptyTagToken):
                if tree.name in XMLTagToken.BR_TAG:
                    fp.write('\n')
            elif isinstance(tree, unicode):
                fp.write(rmsp(tree).encode(self.codec, 'ignore'))
            elif isinstance(tree, WikiSpecialTree):
                pass
            elif isinstance(tree, WikiCommentTree):
                pass
            elif isinstance(tree, WikiXMLTree):
                if tree.xml.name in XMLTagToken.NO_TEXT:
                    pass
                else:
                    if tree.xml.name in XMLTagToken.PAR_TAG:
                        stack.append('\n')
                    for c in reversed(tree):
                        stack.append(c)
            elif isinstance(tree, WikiKeywordTree):
                if tree:
                    if isinstance(tree[0], WikiTree):
                        name = tree[0].get_text()
                    else:
                        name = tree[0]
                    if isinstance(name, unicode) and not isignored(name):
                        stack.append(tree[-1])
            elif isinstance(tree, WikiLinkTree):
                if 2 <= len(tree):
                    for c in reversed(tree[1:]):
                        stack.append(' ')
                        stack.append(c)
                elif tree:
                    stack.append(tree[0])
            elif isinstance(tree, WikiTableCellTree):
                if tree:
                    stack.append('\n')
                    stack.append(tree[-1])
            elif isinstance(tree, WikiTableTree):
                for c in reversed(tree):
                    if not isinstance(c, WikiArgTree):
                        stack.append(c)
            elif isinstance(tree, WikiDivTree):
                stack.append('\n')
                for c in reversed(tree):
                    stack.append(c)
            elif isinstance(tree, WikiTree):
                for c in reversed(tree):
                    stack.append(c)
        return


##  WikiLinkExtractor
##
class WikiLinkExtractor(WikiTextParser):

    def __init__(self, outfp, errfp=sys.stderr, codec='utf-8'):
        WikiTextParser.__init__(self)
        self.outfp = outfp
        self.errfp = errfp
        self.codec = codec
        return

    def close(self):
        self.convert(self.outfp)
        WikiTextParser.close(self)
        return

    def error(self, s):
        self.errfp.write(s)
        return

    def invalid_token(self, pos, token):
        if self.errfp is not None:
            self.error('invalid token(%d): %r\n' % (pos, token))
        return

    def convert(self, fp):
        stack = [self.get_root()]
        while stack:
            tree = stack.pop()
            if isinstance(tree, str):
                fp.write(tree)
            elif isinstance(tree, WikiKeywordTree):
                if tree:
                    if isinstance(tree[0], WikiTree):
                        name = tree[0].get_text()
                    else:
                        name = tree[0]
                    if isinstance(name, unicode):
                        fp.write('keyword\t'+name.encode(self.codec, 'ignore'))
                        if 2 <= len(tree) and not isignored(name):
                            text = tree[-1].get_text()
                            fp.write('\t'+text.encode(self.codec, 'ignore'))
                        fp.write('\n')
            elif isinstance(tree, WikiLinkTree):
                if tree:
                    if isinstance(tree[0], WikiTree):
                        url = tree[0].get_text()
                    else:
                        url = tree[0]
                    if isinstance(url, unicode):
                        fp.write('link\t'+url.encode(self.codec, 'ignore'))
                        if 2 <= len(tree):
                            text = tree[-1].get_text()
                            fp.write('\t'+text.encode(self.codec, 'ignore'))
                        fp.write('\n')
            elif isinstance(tree, WikiTree):
                for c in reversed(tree):
                    stack.append(c)
        return


##  MWDump2Text
##
class MWDump2Text(MWXMLDumpFilter):

    def __init__(self, factory, outfp, titleline=True):
        MWXMLDumpFilter.__init__(self)
        self.factory = factory
        self.outfp = outfp
        self.titleline = titleline
        return

    def open_file(self, pageid, title, revid, timestamp):
        print >>sys.stderr, (pageid, title, revid)
        if self.titleline:
            self.outfp.write(title+'\n')
        self._textparser = self.factory(self.outfp)
        return self.outfp
    
    def close_file(self, fp):
        self._textparser.close()
        self.outfp.write('\f\n')
        return
    
    def write_file(self, fp, text):
        self._textparser.feed_text(text)
        return


##  MWCDB2Text
##
class MWCDB2Text(object):

    def __init__(self, srcpath, dstpath, factory):
        self.reader = CDBReader(srcpath)
        self.writer = CDBMaker(dstpath)
        self.factory = factory
        return

    def close(self):
        self.writer.finish()
        return

    def convert(self, pageid, revision=0):
        key = '%d/%d:text' % (pageid, revision)
        srcbuf = StringIO(self.reader[key])
        src = GzipFile(mode='r', fileobj=srcbuf)
        dstbuf = StringIO()
        dst = GzipFile(mode='w', fileobj=dstbuf)
        textparser = self.factory(dst)
        textparser.feed_text(src.read().decode(textparser.codec))
        textparser.close()
        src.close()
        dst.close()
        self.writer.add(key, dstbuf.getvalue())
        return

    def convert_all(self):
        for key in self.reader:
            (id,_,type) = key.partition(':')
            if type == 'text':
                try:
                    (pageid,_,revision) = id.partition('/')
                    pageid = int(pageid)
                    revision = int(revision)
                except ValueError:
                    continue
                print >>sys.stderr, (pageid,revision)
                self.convert(pageid, revision)
            else:
                self.writer.add(key, self.reader[key])
        return


# main
def main(argv):
    import getopt
    def getfp(path, mode='r'):
        if path == '-' and mode == 'r':
            return (path, sys.stdin)
        elif path == '-' and mode == 'w':
            return (path, sys.stdout)
        elif path.endswith('.gz'):
            return (path[:-3], GzipFile(path, mode=mode))
        elif path.endswith('.bz2'):
            return (path[:-4], BZ2File(path, mode=mode))
        else:
            return (path, open(path, mode=mode+'b'))
    def usage():
        print ('usage: %s [-o output] [-c codec] [-C cdbdump] [-T] [-L] '
               '[file ...]') % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'o:c:C:TL')
    except getopt.GetoptError:
        return usage()
    output = None
    codec = 'utf-8'
    cdbdump = None
    titleline = False
    klass = WikiTextExtractor
    for (k, v) in opts:
        if k == '-o': output = v
        elif k == '-c': codec = v 
        elif k == '-C': cdbdump = v 
        elif k == '-T': titleline = True
        elif k == '-L': klass = WikiLinkExtractor
    factory = (lambda outfp: klass(outfp, codec=codec))
    if cdbdump is not None:
        if not output: return usage()
        reader = MWCDB2Text(cdbdump, output, factory)
        if args:
            for pageid in args:
                reader.convert(int(pageid))
        else:
            try:
                reader.convert_all()
            finally:
                reader.close()
    else:
        (_,outfp) = getfp(output or '-', 'w')
        for path in (args or ['-']):
            (path,fp) = getfp(path)
            if path.endswith('.xml'):
                parser = MWDump2Text(factory, outfp, titleline=titleline)
            else:
                parser = factory(outfp)
            parser.feed_file(fp)
            fp.close()
            parser.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
