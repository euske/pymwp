#!/usr/bin/env python
import sys
from xml.parsers.expat import ParserCreate


##  MWXMLDumpParser
##
class MWXMLDumpParser:

    def __init__(self):
        self._expat = ParserCreate()
        self._expat.StartElementHandler = self.start_element
        self._expat.EndElementHandler = self.end_element
        self._expat.CharacterDataHandler = self.handle_data
        self._handler = None
        self._stack = []
        return

    def close(self):
        return

    def feed_file(self, fp):
        self._expat.ParseFile(fp.buffer)
        return

    def start_element(self, name, attrs):
        if name == 'page':
            self._revid = None
        elif name == 'revision':
            if self._revid is None:
                self.start_page(self._pageid, self._title)
        elif name == 'id':
            if self._stack[-1] == 'page':
                self._pageid = ''
                self._handler = self._handle_pageid
            elif self._stack[-1] == 'revision':
                self._revid = ''
                self._handler = self._handle_revid
        elif name == 'title':
            if self._stack[-1] == 'page':
                self._title = ''
                self._handler = self._handle_title
        elif name == 'timestamp':
            if self._stack[-1] == 'revision':
                self._timestamp = ''
                self._handler = self._handle_timestamp
        elif name == 'text':
            if self._stack[-1] == 'revision':
                self.start_revision(self._pageid, self._title, self._revid, self._timestamp)
                self._handler = self.handle_text
        self._stack.append(name)
        return

    def end_element(self, name):
        self._stack.pop()
        self._handler = None
        if name == 'page':
            self.end_page(self._pageid, self._title)
        elif name == 'revision':
            self.end_revision(self._pageid, self._title, self._revid, self._timestamp)
        return

    def handle_data(self, data):
        if self._handler is not None:
            self._handler(data)
        return

    def _handle_pageid(self, data):
        self._pageid += data
        return
    def _handle_title(self, data):
        self._title += data
        return
    def _handle_revid(self, data):
        self._revid += data
        return
    def _handle_timestamp(self, data):
        self._timestamp += data
        return

    def start_page(self, pageid, title):
        return
    def end_page(self, pageid, title):
        return
    def start_revision(self, pageid, title, revid, timestamp):
        return
    def end_revision(self, pageid, title, revid, timestamp):
        return
    def handle_text(self, text):
        return


##  MWXMLDumpFilter
##
class MWXMLDumpFilter(MWXMLDumpParser):

    def __init__(self):
        MWXMLDumpParser.__init__(self)
        self._ok = False
        self._fp = None
        return

    def start_page(self, pageid, title):
        MWXMLDumpParser.start_page(self, pageid, title)
        self._ok = self.accept_page(pageid, title)
        return

    def end_page(self, pageid, title):
        MWXMLDumpParser.end_page(self, pageid, title)
        return

    def start_revision(self, pageid, title, revid, timestamp):
        MWXMLDumpParser.start_revision(self, pageid, title, revid, timestamp)
        if self._ok:
            self._fp = self.open_file(pageid, title, revid, timestamp)
        return

    def end_revision(self, pageid, title, revid, timestamp):
        MWXMLDumpParser.end_revision(self, pageid, title, revid, timestamp)
        if self._fp is not None:
            self.close_file(self._fp)
            self._fp = None
        return

    def handle_text(self, text):
        MWXMLDumpParser.handle_text(self, text)
        if self._fp is not None:
            self.write_file(self._fp, text)
        return

    def accept_page(self, pageid, title):
        return True

    def open_file(self, pageid, title, revid, timestamp):
        raise NotImplementedError
    def close_file(self, fp):
        raise NotImplementedError
    def write_file(self, fp, text):
        raise NotImplementedError


# main
def main(argv):
    from utils import getfp
    class TitleExtractor(MWXMLDumpParser):
        def start_revision(self, pageid, title, revid, timestamp):
            print(pageid, title)
            return
    args = argv[1:] or ['-']
    for path in args:
        print(path, file=sys.stderr)
        (_,fp) = getfp(path)
        parser = TitleExtractor()
        parser.feed_file(fp)
        parser.close()
        fp.close()
    return 0

if __name__ == '__main__': sys.exit(main(sys.argv))
