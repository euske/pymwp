#!/usr/bin/env python2
# -*- coding: euc-jp -*-
import re
import sys
from pymwp.mwtokenizer import WikiToken
from pymwp.mwparser import WikiTextParser
from pymwp.mwparser import WikiTree, WikiXMLTree, WikiCommentTree
from pymwp.mwparser import WikiSpecialTree, WikiKeywordTree, WikiLinkTree
from pymwp.mwparser import WikiPreTree, WikiItemizeTree, WikiHeadlineTree
from pymwp.mwparser import WikiTableCaptionTree, WikiTableHeaderTree, WikiTableDataTree
from pymwp.mwxmldump import MWXMLDumpSplitter


SPC = re.compile(r'\s+')
def rmsp(s): return SPC.sub(' ', s)
MEDIA_JP = re.compile(ur'^(file|image|media|ファイル|画像):', re.I)
def ismedia(name): return MEDIA_JP.match(name)


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
            if tree.name == 'ref':
                pass
            else:
                for c in tree:
                    self.dump(c)
        elif isinstance(tree, WikiKeywordTree):
            if 2 <= len(tree):
                name = tree[0]
                if isinstance(name, WikiTree):
                    name = name.get_text()
                if ismedia(name):
                    self.dump(tree[-1])
                else:
                    for c in tree[1:]:
                        self.dump(c)
            elif tree:
                self.dump(tree[0])
        elif isinstance(tree, WikiLinkTree):
            if 2 <= len(tree):
                for c in tree[1:]:
                    self.dump(c)
                    self.write(' ')
            elif tree:
                self.dump(tree[0])
        elif isinstance(tree, WikiTree):
            for c in tree:
                self.dump(c)
            if (isinstance(tree, WikiPreTree) or
                isinstance(tree, WikiItemizeTree) or
                isinstance(tree, WikiHeadlineTree) or
                isinstance(tree, WikiTableCaptionTree) or
                isinstance(tree, WikiTableHeaderTree) or
                isinstance(tree, WikiTableDataTree)):
                self.write('\n')
        return


##  MWDump2Text
##
class MWDump2Text(MWXMLDumpSplitter):

    def __init__(self, output=sys.stdout, template=None,
                 titlepat=None, pageids=None,
                 revisionlimit=1, codec='utf-8'):
        MWXMLDumpSplitter.__init__(
            self, output=output, template=template,
            titlepat=titlepat, pageids=pageids,
            revisionlimit=revisionlimit, codec=codec)
        return

    def start_revision(self, pageid, title, revision):
        MWXMLDumpSplitter.start_revision(self, pageid, title, revision)
        fp = self.get_fp()
        if fp is not None:
            self._textparser = WikiTextExtractor(outfp=fp, codec=self.codec)
        return
    
    def handle_text(self, text):
        if self._textparser is not None:
            self._textparser.feed_text(text)
        return
    
    def end_revision(self):
        if self._textparser is not None:
            self._textparser.close()
            self._textparser = None
        MWXMLDumpSplitter.end_revision(self)
        return


# main
def main(argv):
    import getopt
    def usage():
        print ('usage: %s [-c codec] [-t template] [-e titlepat] [-n npages] '
               '[-p pageids] [-r revisionlimit] [file ...]') % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'c:t:e:n:p:r:')
    except getopt.GetoptError:
        return usage()
    codec = 'utf-8'
    template = None
    titlepat = None
    pageids = None
    revisionlimit = 1
    for (k, v) in opts:
        if k == '-c': codec = v 
        elif k == '-t': template = v
        elif k == '-e': titlepat = re.compile(v)
        elif k == '-n':
            pageids = set(xrange(int(v)))
        elif k == '-p':
            if pageids is None:
                pageids = set()
            for x in v.split(','):
                pageids.add(int(x))
        elif k == '-r': revisionlimit = int(v)
    for path in (args or ['-']):
        if path == '-':
            fp = sys.stdin
            parser = WikiTextExtractor(codec=codec)
        elif path.endswith('.gz'):
            from gzip import GzipFile
            fp = GzipFile(path)
            parser = MWDump2Text(
                codec=codec, template=template,
                titlepat=titlepat, pageids=pageids,
                revisionlimit=revisionlimit)
        elif path.endswith('.bz2'):
            from bz2 import BZ2File
            fp = BZ2File(path)
            parser = MWDump2Text(
                codec=codec, template=template,
                titlepat=titlepat, pageids=pageids,
                revisionlimit=revisionlimit)
        else:
            fp = open(path)
            parser = WikiTextExtractor(codec=codec)
        parser.feed_file(fp)
        fp.close()
        parser.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
