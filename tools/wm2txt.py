#!/usr/bin/env python2
import sys

##  WPXMLTextParser
##
class WPXMLTextParser(WPXMLParser):

    def __init__(self):
        WPXMLParser.__init__(self)
        self._textparser = None
        return
    def start_text(self):
        self._textparser = WikiTextParser()
        return
    def end_text(self):
        self._textparser.close()
        return
    def handle_text(self, text):
        self._textparser.feed_text(data)
        return
    def handle_revision(self, title, revision):
        if revision != 0: return
        tree = self._textparser.get_root()
        #print >>sys.stderr, title
        def f(x):
            if x is WikiToken.PAR:
                sys.stdout.write('\n')
            elif isinstance(x, WikiTree):
                for c in x:
                    f(c)
                if (isinstance(x, WikiPreTree) or
                    isinstance(x, WikiBulletTree) or
                    isinstance(x, WikiHeadlineTree)):
                    sys.stdout.write('\n')
            elif isinstance(x, unicode):
                sys.stdout.write(x.encode('utf'))
        f(tree)
        print
        return


if __name__ == '__main__': sys.exit(main(sys.argv))
