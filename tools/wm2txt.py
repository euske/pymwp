#!/usr/bin/env python2
import sys
from pymwp.mwparser import WikiTextParser
from pymwp.mwparser import WikiTree, WikiPreTree, WikiItemizeTree, WikiHeadlineTree
from pymwp.mwtokenizer import WikiToken
from pymwp.mwxmldump import MWXMLParser


##  WikiTextExtractor
##
class WikiTextExtractor(WikiTextParser):

    def __init__(self, outfp=sys.stdout, errfp=sys.stderr):
        WikiTextParser.__init__(self)
        self.outfp = outfp
        self.errfp = errfp
        return

    def invalid_token(self, token):
        self.errfp.write('invalid token: %r\n' % token)
        return

    def close(self):
        WikiTextParser.close(self)
        tree = self.get_root()
        def f(x):
            if x is WikiToken.PAR:
                self.outfp.write('\n')
            elif isinstance(x, WikiTree):
                for c in x:
                    f(c)
                if (isinstance(x, WikiPreTree) or
                    isinstance(x, WikiItemizeTree) or
                    isinstance(x, WikiHeadlineTree)):
                    self.outfp.write('\n')
            elif isinstance(x, unicode):
                self.outfp.write(x.encode('utf'))
        f(tree)
        return


##  MWXMLTextExtractor
##
class MWXMLTextExtractor(MWXMLParser):

    def __init__(self):
        MWXMLParser.__init__(self)
        self._textparser = None
        return
    
    def start_revision(self, title, revision):
        if revision == 0:
            self._textparser = WikiTextParser()
        return
    
    def handle_text(self, text):
        if self._textparser is not None:
            self._textparser.feed_text(text)
        return
    
    def end_revision(self):
        if self._textparser is not None:
            self._textparser.close()
            self._textparser = None
        return

# main
def main(argv):
    args = argv[1:] or ['-']
    for path in args:
        print >>sys.stderr, '==', path
        parser = WikiTextExtractor()
        if path == '-':
            fp = sys.stdin
        elif path.endswith('.gz'):
            from gzip import GzipFile
            fp = GzipFile(path)
            parser = MWXMLTextExtractor()
        elif path.endswith('.bz2'):
            from bz2 import BZ2File
            fp = BZ2File(path)
            parser = MWXMLTextExtractor()
        else:
            fp = open(path)
        parser.feed_file(fp)
        fp.close()
        parser.close()
    return 0

if __name__ == '__main__': sys.exit(main(sys.argv))
