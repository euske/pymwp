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
from pymwp.mwtokenizer import WikiToken
from pymwp.mwparser import WikiTextParser
from pymwp.mwparser import WikiTree, WikiXMLTree, WikiArgTree
from pymwp.mwparser import WikiSpecialTree, WikiCommentTree
from pymwp.mwparser import WikiKeywordTree, WikiLinkTree
from pymwp.mwparser import WikiSpanTree, WikiDivTree
from pymwp.mwparser import WikiTableTree, WikiTableCellTree
from pymwp.mwxmldump import MWXMLDumpFilter
from pymwp.pycdb import CDBReader


SPC = re.compile(r'\s+')
def rmsp(s): return SPC.sub(' ', s)

IGNORED = re.compile(u'^([-a-z]+|Category|Special):')
def isignored(name): return IGNORED.match(name)


##  WikiTextExtractor
##
class WikiTextExtractor(WikiTextParser):

    def __init__(self, errfp=sys.stderr, codec='utf-8'):
        WikiTextParser.__init__(self)
        self.errfp = errfp
        self.codec = codec
        return

    def error(self, s):
        self.errfp.write(s)
        return

    def invalid_token(self, pos, token):
        if self.errfp is not None:
            self.error('invalid token(%d): %r\n' % (pos, token))
        return

    def dump(self, fp, tree=None):
        if tree is None:
            self.dump(fp, self.get_root())
        elif tree is WikiToken.PAR:
            fp.write('\n')
        elif isinstance(tree, unicode):
            fp.write(rmsp(tree).encode(self.codec, 'ignore'))
        elif isinstance(tree, WikiSpecialTree):
            pass
        elif isinstance(tree, WikiCommentTree):
            pass
        elif isinstance(tree, WikiXMLTree):
            if tree.xml.name == 'ref':
                pass
            elif tree.xml.name == 'br':
                fp.write('\n')
            else:
                for c in tree:
                    self.dump(fp, c)
        elif isinstance(tree, WikiKeywordTree):
            if tree:
                if isinstance(tree[0], WikiTree):
                    name = tree[0].get_text()
                else:
                    name = tree[0]
                if isinstance(name, unicode) and not isignored(name):
                    self.dump(fp, tree[-1])
        elif isinstance(tree, WikiLinkTree):
            if 2 <= len(tree):
                for c in tree[1:]:
                    self.dump(fp, c)
                    fp.write(' ')
            elif tree:
                self.dump(fp, tree[0])
        elif isinstance(tree, WikiTableCellTree):
            if tree:
                self.dump(fp, tree[-1])
                fp.write('\n')
        elif isinstance(tree, WikiTableTree):
            for c in tree:
                if not isinstance(c, WikiArgTree):
                    self.dump(fp, c)
        elif isinstance(tree, WikiDivTree):
            for c in tree:
                self.dump(fp, c)
            fp.write('\n')
        elif isinstance(tree, WikiTree):
            for c in tree:
                self.dump(fp, c)
        return


##  WikiLinkExtractor
##
class WikiLinkExtractor(WikiTextParser):

    def __init__(self, errfp=sys.stderr, codec='utf-8'):
        WikiTextParser.__init__(self)
        self.errfp = errfp
        self.codec = codec
        return

    def error(self, s):
        self.errfp.write(s)
        return

    def invalid_token(self, pos, token):
        if self.errfp is not None:
            self.error('invalid token(%d): %r\n' % (pos, token))
        return

    def dump(self, fp, tree=None):
        if tree is None:
            self.dump(fp, self.get_root())
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
            for c in tree:
                self.dump(fp, c)
        return


##  MWDump2Text
##
class MWDump2Text(MWXMLDumpFilter):

    def __init__(self, factory,
                 output=sys.stdout, codec='utf-8', titleline=True,
                 titlepat=None, revisionlimit=1):
        MWXMLDumpSplitter.__init__(
            self,
            titlepat=titlepat, revisionlimit=revisionlimit)
        self.factory = factory
        self.codec = codec
        self.output = output
        self.titleline = titleline
        return

    def open_file(self, pageid, title, revision):
        print >>sys.stderr, pageid
        if self.titleline:
            self.write(title+'\n')
        self._textparser = self.factory(self.codec)
        return self.output
    
    def write_file(self, fp, text):
        self._textparser.feed_text(text)
        return
    
    def close_file(self, fp):
        self._textparser.close()
        self._textparser.dump(fp)
        self.write('\f\n')
        return


##  MWCDB2Text
##
class MWCDB2Text(object):


    def __init__(self, path, factory,
                 output=sys.stdout, 
                 codec='utf-8',
                 titleline=True,
                 titlepat=None, revisionlimit=1):
        self.reader = CDBReader(path)
        self.factory = factory
        self.codec = codec
        self.output = output
        self.titleline = titleline
        return

    def dump(self, title, revision=0):
        key = '%s:%d' % (title.encode('utf-8'), revision)
        buf = StringIO(self.reader[key])
        fp = GzipFile(mode='r', fileobj=buf)
        textparser = self.factory(self.codec)
        textparser.feed_text(fp.read().decode('utf-8'))
        textparser.close()
        self.output.write(title.encode(self.codec, 'ignore'))
        textparser.dump(self.output)
        self.output.write('\f\n')
        return

    def dumpall(self):
        for key in self.reader:
            i = key.rindex(':')
            title = key[:i].decode('utf-8')
            revision = int(key[i+1:])
            self.dump(title, revision)
        return


# main
def main(argv):
    import getopt
    def getfp(path):
        if path == '-':
            return sys.stdin
        elif path.endswith('.gz'):
            return GzipFile(path)
        elif path.endswith('.bz2'):
            return BZ2File(path)
        else:
            return open(path, 'rb')
    def usage():
        print ('usage: %s [-X xmldump] [-C cdbdump] [-c codec] [-T] [-L] '
               '[-e titlepat] [-r revisionlimit] [file ...]') % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'X:C:c:TLe:r:')
    except getopt.GetoptError:
        return usage()
    xmldump = None
    cdbdump = None
    codec = 'utf-8'
    titlepat = None
    revisionlimit = 1
    titleline = False
    output = sys.stdout
    factory = (lambda codec: WikiTextExtractor(codec=codec))
    for (k, v) in opts:
        if k == '-X': xmldump = v
        elif k == '-C': cdbdump = v
        elif k == '-c': codec = v 
        elif k == '-T': titleline = True
        elif k == '-L': factory = (lambda codec: WikiLinkExtractor(codec=codec))
        elif k == '-e': titlepat = re.compile(v)
        elif k == '-r': revisionlimit = int(v)
    if xmldump is not None:
        parser = MWDump2Text(
            factory, output=output, codec=codec, titleline=titleline,
            titlepat=titlepat, revisionlimit=revisionlimit)
        fp = getfp(xmldump)
        parser.feed_file(fp)
        fp.close()
        parser.close()
    elif cdbdump is not None:
        reader = MWCDB2Text(
            cdbdump, factory, output=output, codec=codec, titleline=titleline,
            titlepat=titlepat, revisionlimit=revisionlimit)
        if args:
            for title in args:
                reader.dump(title.decode('utf-8'))
        else:
            reader.dumpall()
    else:
        for path in (args or ['-']):
            parser = factory(codec)
            fp = getfp(path)
            parser.feed_file(fp)
            fp.close()
            parser.close()
            parser.dump(output)
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
