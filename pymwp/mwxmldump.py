#!/usr/bin/env python2
import sys
from xml.parsers.expat import ParserCreate


##  MWXMLParser
##
class MWXMLParser(object):
    
    def __init__(self):
        self._expat = ParserCreate()
        self._expat.StartElementHandler = self.start_element
        self._expat.EndElementHandler = self.end_element
        self._expat.CharacterDataHandler = self.handle_data
        self._titleok = self._textok = False
        return
    
    def feed_file(self, fp):
        self._expat.ParseFile(fp)
        return
        
    def start_element(self, name, attrs):
        if name == 'page':
            self._revision = 0
            self._titleok = False
            self.start_page()
        elif name == 'title':
            self._titleok = True
            self._title = u''
        elif name == 'revision':
            self.start_revision(self._title, self._revision)
        elif name == 'text':
            self._textok = True
        return
    
    def end_element(self, name):
        if name == 'text':
            self._textok = False
        elif name == 'revision':
            self.end_revision()
            self._revision += 1
        elif name == 'title':
            self._titleok = False
        elif name == 'page':
            self.end_page()
        return
    
    def handle_data(self, data):
        if self._textok:
            self.handle_text(data)
        elif self._titleok:
            self._title += data
        return

    def start_page(self):
        return
    def end_page(self):
        return
    def start_revision(self, title, revision):
        return
    def end_revision(self):
        return
    def handle_text(self, text):
        return


# main
def main(argv):
    args = argv[1:] or ['-']
    class Parser(MWXMLParser):
        def start_revision(self, title, revision):
            sys.stdout.write(title.encode('utf-8')+'\n')
            return
        def end_revision(self):
            sys.stdout.write('\f')
            return
        def handle_text(self, text):
            sys.stdout.write(text.encode('utf-8'))
            return
    for path in args:
        print >>sys.stderr, path
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
        parser = Parser()
        parser.feed_file(fp)
        fp.close()
        parser.close()
    return 0

if __name__ == '__main__': sys.exit(main(sys.argv))
