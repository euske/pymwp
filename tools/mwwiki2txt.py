#!/usr/bin/env python2
#
# usage:
#  $ mwwiki2txt.py -n10 -t 'article%(pageid)05d.txt' jawiki.xml.bz2
#
import re
import sys
from pymwp.mwtokenizer import WikiToken
from pymwp.mwparser import WikiTextParser
from pymwp.mwparser import WikiTree, WikiXMLTree, WikiArgTree
from pymwp.mwparser import WikiSpecialTree, WikiCommentTree
from pymwp.mwparser import WikiKeywordTree, WikiLinkTree
from pymwp.mwparser import WikiSpanTree, WikiDivTree
from pymwp.mwparser import WikiTableTree, WikiTableCellTree
from pymwp.mwxmldump import MWXMLDumpSplitter


SPC = re.compile(r'\s+')
def rmsp(s): return SPC.sub(' ', s)

IGNORED = re.compile(u'^([-a-z]+|Category|Special):')
def isignored(name): return IGNORED.match(name)


##  WikiTextExtractor
##
class WikiTextExtractor(WikiTextParser):

    def __init__(self, outfp=sys.stdout, errfp=sys.stderr, codec='utf-8'):
        WikiTextParser.__init__(self)
        self.outfp = outfp
        self.errfp = errfp
        self.codec = codec
        return

    def write(self, s):
        self.outfp.write(s.encode(self.codec, 'ignore'))
        return

    def error(self, s):
        self.errfp.write(s)
        return

    def close(self):
        WikiTextParser.close(self)
        self.dump(self.get_root())
        return

    def invalid_token(self, pos, token):
        if self.errfp is not None:
            self.error('invalid token(%d): %r\n' % (pos, token))
        return

    def dump(self, tree):
        if tree is WikiToken.PAR:
            self.write('\n')
        elif isinstance(tree, unicode):
            self.write(rmsp(tree))
        elif isinstance(tree, WikiSpecialTree):
            pass
        elif isinstance(tree, WikiCommentTree):
            pass
        elif isinstance(tree, WikiXMLTree):
            if tree.xml.name == 'ref':
                pass
            else:
                for c in tree:
                    self.dump(c)
        elif isinstance(tree, WikiKeywordTree):
            if tree:
                if isinstance(tree[0], WikiTree):
                    name = tree[0].get_text()
                else:
                    name = tree[0]
                if isinstance(name, unicode) and not isignored(name):
                    self.dump(tree[-1])
        elif isinstance(tree, WikiLinkTree):
            if 2 <= len(tree):
                for c in tree[1:]:
                    self.dump(c)
                    self.write(' ')
            elif tree:
                self.dump(tree[0])
        elif isinstance(tree, WikiTableCellTree):
            if tree:
                self.dump(tree[-1])
                self.write('\n')
        elif isinstance(tree, WikiTableTree):
            for c in tree:
                if not isinstance(c, WikiArgTree):
                    self.dump(c)
        elif isinstance(tree, WikiDivTree):
            for c in tree:
                self.dump(c)
            self.write('\n')
        elif isinstance(tree, WikiTree):
            for c in tree:
                self.dump(c)
        return


##  MWDump2Text
##
class MWDump2Text(MWXMLDumpSplitter):

    def __init__(self, factory,
                 output=sys.stdout, template=None,
                 titlepat=None, pageids=None,
                 revisionlimit=1, codec='utf-8',
                 titleline=True):
        MWXMLDumpSplitter.__init__(
            self, output=output, template=template,
            titlepat=titlepat, pageids=pageids,
            revisionlimit=revisionlimit, codec=codec)
        self.factory = factory
        self.titleline = titleline
        return

    def start_revision(self, pageid, title, revision):
        print >>sys.stderr, pageid
        MWXMLDumpSplitter.start_revision(self, pageid, title, revision)
        if self.titleline:
            self.write(title+'\n')
        fp = self.get_fp()
        if fp is not None:
            self._textparser = self.factory(fp, self.codec)
        return
    
    def handle_text(self, text):
        if self._textparser is not None:
            self._textparser.feed_text(text)
        return
    
    def end_revision(self):
        if self._textparser is not None:
            self._textparser.close()
            self._textparser = None
        self.write('\f\n')
        MWXMLDumpSplitter.end_revision(self)
        return


# main
def main(argv):
    import getopt
    def usage():
        print ('usage: %s [-x] [-c codec] [-t template] [-e titlepat] [-n npages] '
               '[-p pageids] [-r revisionlimit] [-T] [file ...]') % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'xc:t:e:n:p:r:T')
    except getopt.GetoptError:
        return usage()
    codec = 'utf-8'
    template = None
    titlepat = None
    pageids = None
    xmldump = False
    revisionlimit = 1
    titleline = False
    for (k, v) in opts:
        if k == '-x': xmldump = True
        elif k == '-c': codec = v 
        elif k == '-t': template = v
        elif k == '-e': titlepat = re.compile(v)
        elif k == '-r': revisionlimit = int(v)
        elif k == '-n':
            pageids = set(xrange(int(v)))
        elif k == '-p':
            if pageids is None:
                pageids = set()
            for x in v.split(','):
                pageids.add(int(x))
        elif k == '-T':
            titleline = True
    factory = (lambda fp,codec: WikiTextExtractor(outfp=fp, codec=codec))
    for path in (args or ['-']):
        if path == '-':
            fp = sys.stdin
        elif path.endswith('.gz'):
            from gzip import GzipFile
            fp = GzipFile(path)
        elif path.endswith('.bz2'):
            from bz2 import BZ2File
            fp = BZ2File(path)
        else:
            fp = open(path)
        if xmldump:
            parser = MWDump2Text(
                factory,
                codec=codec, template=template,
                titlepat=titlepat, pageids=pageids,
                revisionlimit=revisionlimit,
                titleline=titleline)
        else:
            parser = factory(sys.stdout, codec)
        parser.feed_file(fp)
        fp.close()
        parser.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
