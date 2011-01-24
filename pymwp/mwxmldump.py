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


##  MWXMLDumpSplitter
##
class MWXMLDumpSplitter(MWXMLDumpParser):

    def __init__(self, output=sys.stdout, codec='utf-8',
                 template=None, titlepat=None,
                 pageids=None, revisionlimit=1):
        MWXMLDumpParser.__init__(self)
        self.codec = codec
        self.output = output
        self.template = template
        self.titlepat = titlepat
        self.pageids = pageids
        self.revisionlimit = revisionlimit
        self._fp = None
        return

    def get_fp(self):
        return self._fp

    def write(self, text):
        if self._fp is not None:
            self._fp.write(text.encode(self.codec, 'ignore'))
        return

    def start_revision(self, pageid, title, revision):
        if self.pageids is not None:
            if pageid not in self.pageids: return
        if self.titlepat is not None:
            if not self.titlepat.search(title): return
        if self.revisionlimit <= revision: return
        if self.template is not None:
            name = title.encode('utf-8').encode('quopri_codec')
            path = (self.template % {'name':name, 'pageid':pageid, 'revision':revision})
            self._fp = open(path, 'w')
        elif self.output is not None:
            self._fp = self.output
        return
    
    def end_revision(self):
        if self._fp is not None:
            if self.template is not None:
                self._fp.close()
            self._fp = None
        return
    
    def handle_text(self, text):
        self.write(text)
        return


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
