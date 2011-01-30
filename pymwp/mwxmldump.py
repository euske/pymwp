#!/usr/bin/env python2
import sys
from xml.parsers.expat import ParserCreate


##  MWXMLDumpParser
##
class MWXMLDumpParser(object):
    
    def __init__(self):
        self._expat = ParserCreate()
        self._expat.StartElementHandler = self.start_element
        self._expat.EndElementHandler = self.end_element
        self._expat.CharacterDataHandler = self.handle_data
        self._titleok = self._textok = False
        self._pageid = 0
        return

    def close(self):
        return
    
    def feed_file(self, fp):
        self._expat.ParseFile(fp)
        return
        
    def start_element(self, name, attrs):
        if name == 'page':
            self._revision = 0
            self._titleok = False
        elif name == 'title':
            self._titleok = True
            self._title = u''
        elif name == 'revision':
            self.start_revision(self._pageid, self._title, self._revision)
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
            self.start_page(self._pageid, self._title)
        elif name == 'page':
            self.end_page()
            self._pageid += 1
        return
    
    def handle_data(self, data):
        if self._textok:
            self.handle_text(data)
        elif self._titleok:
            self._title += data
        return

    def start_page(self, pageid, title):
        return
    def end_page(self):
        return
    def start_revision(self, pageid, title, revision):
        return
    def end_revision(self):
        return
    def handle_text(self, text):
        return


##  MWXMLDumpFilter
##
class MWXMLDumpFilter(MWXMLDumpParser):

    def __init__(self, titlepat=None, revisionlimit=1):
        MWXMLDumpParser.__init__(self)
        self.titlepat = titlepat
        self.revisionlimit = revisionlimit
        self._fp = None
        return

    def start_revision(self, pageid, title, revision):
        if self.revisionlimit <= revision: return
        if self.titlepat is not None:
            if not self.titlepat.search(title): return
        self._fp = self.open_file(pageid, title, revision)
        return
    
    def end_revision(self):
        if self._fp is not None:
            self.close_file(self._fp)
            self._fp = None
        return
    
    def handle_text(self, text):
        if self._fp is not None:
            self.write_file(self._fp, text)
        return

    def open_file(self, pageid, title, revision):
        raise NotImplementedError
    def close_file(self, fp):
        raise NotImplementedError
    def write_file(self, fp, text):
        raise NotImplementedError


# main
def main(argv):
    args = argv[1:] or ['-']
    class TitleExtractor(MWXMLDumpParser):
        def start_revision(self, pageid, title, revision):
            print pageid, title.encode('utf-8')
            return
    for path in args:
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
        parser = TitleExtractor()
        parser.feed_file(fp)
        fp.close()
        parser.close()
    return 0

if __name__ == '__main__': sys.exit(main(sys.argv))
