#!/usr/bin/env python
import sys
from gzip import GzipFile
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from pycdb import CDBReader
from pycdb import CDBMaker


##  WikiDBReader
##
class WikiDBReader(object):

    def __init__(self, path, gzip=True, codec='utf-8'):
        self._reader = CDBReader(path)
        self.gzip = gzip
        self.codec = codec
        return

    def __iter__(self):
        return self.get_pages()

    def __getitem__(self, pageid):
        return self.get_page(pageid)

    def _get_data(self, key):
        data = self._reader[key]
        if key.endswith('.gz'):
            fp = StringIO(data)
            data = GzipFile(mode='r', fileobj=fp).read()
        return data.decode(self.codec, 'ignore')

    def get_pages(self):
        for key in self._reader.iterkeys():
            if key.endswith(':title'):
                (pageid,_,title) = key.partition(':')
                yield (int(pageid), title.decode(self.codec, 'ignore'))
        return

    def get_page(self, pageid):
        key = ('%s:title' % pageid)
        title = self._reader[key].decode(self.codec, 'ignore')
        key = ('%s:revs' % pageid)
        revids = self._reader[key].split(' ')
        return (title, revids)

    def get_wiki(self, pageid, revid):
        key = '%s/%s:wiki' % (pageid, revid)
        if self.gzip:
            key += '.gz'
        return self._get_data(key)

    def get_text(self, pageid, revid):
        key = '%s/%s:text' % (pageid, revid)
        if self.gzip:
            key += '.gz'
        return self._get_data(key)


##  WikiDBWriter
##
class WikiDBWriter(object):

    def __init__(self, path, gzip=True, codec='utf-8'):
        self._maker = CDBMaker(path)
        self.gzip = gzip
        self.codec = codec
        self._pageid = None
        self._revids = []
        return

    def _add_data(self, key, value):
        data = value.encode(self.codec, 'ignore')
        if key.endswith('.gz'):
            fp = StringIO()
            GzipFile(mode='w', fileobj=fp).write(data)
            data = fp.getvalue()
        self._maker.add(key, data)
        return

    def _flush_page(self, pageid):
        if self._pageid != pageid:
            if self._revids:
                revs = ' '.join( str(revid) for revid in self._revids )
                self._maker.add('%s:revs' % pageid, revs)
            self._revids = []
            self._pageid = pageid
        return

    def get_size(self):
        return self._maker.get_size()

    def close(self):
        self._flush_page(None)
        self._maker.finish()
        return

    def add_page(self, pageid, title):
        self._flush_page(pageid)
        self._maker.add('%s:title' % pageid, title.encode('utf-8'))
        return

    def add_revid(self, pageid, revid):
        assert self._pageid == pageid
        self._revids.append(revid)
        return

    def add_wiki(self, pageid, revid, wiki):
        self.add_revid(pageid, revid)
        key = '%s/%s:wiki' % (pageid, revid)
        if self.gzip:
            key += '.gz'
        self._add_data(key, wiki)
        return

    def add_text(self, pageid, revid, wiki):
        self.add_revid(pageid, revid)
        key = '%s/%s:text' % (pageid, revid)
        if self.gzip:
            key += '.gz'
        self._add_data(key, wiki)
        return


# main
def main(argv):
    args = argv[1:]
    for path in args:
        reader = WikiDBReader(path)
        for (pageid,title) in reader:
            print (pageid, title)
            (_,revids) = reader[pageid]
            for revid in revids:
                wiki = reader.get_wiki(pageid, revid)
                print wiki.encode('utf-8')
            print
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
