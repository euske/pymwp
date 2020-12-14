#!/usr/bin/env python
import sys
from .pycdb import CDBReader
from .pycdb import CDBMaker
from .utils import compress, decompress, getfp


##  WikiDBReader
##
class WikiDBReader(object):

    def __init__(self, path, ext='', encoding='utf-8'):
        self._reader = CDBReader(path)
        self.ext = ext
        self.encoding = encoding
        return

    def __iter__(self):
        return self.get_pageids()

    def __getitem__(self, pageid):
        return self.get_page(pageid)

    def _get_data(self, key):
        data = self._reader[key.encode(self.encoding)]
        data = decompress(key, data)
        return data.decode(self.encoding)

    def get_pageids(self):
        for key in self._reader.iterkeys():
            key = key.decode(self.encoding)
            if key.endswith(':title'):
                (pageid,_,_) = key.partition(':')
                yield int(pageid)
        return

    def get_page(self, pageid):
        key = ('%s:title' % pageid).encode(self.encoding)
        title = self._reader[key].decode(self.encoding)
        key = ('%s:revs' % pageid).encode(self.encoding)
        revids = self._reader[key].decode(self.encoding).split(' ')
        return (title, revids)

    def get_wiki(self, pageid, revid):
        key = '%s/%s:wiki' % (pageid, revid)
        key += self.ext
        return self._get_data(key)

    def get_text(self, pageid, revid):
        key = '%s/%s:text' % (pageid, revid)
        key += self.ext
        return self._get_data(key)


##  WikiDBWriter
##
class WikiDBWriter(object):

    def __init__(self, pathpat, ext='', encoding='utf-8', maxsize=2**31):
        self.pathpat = pathpat
        self.ext = ext
        self.encoding = encoding
        self.maxsize = maxsize
        self._index = 0
        self._maker = None
        self._pageid = None
        self._revids = []
        return

    def _new_page(self, pageid):
        if self._pageid != pageid:
            if self._revids:
                revs = ' '.join( str(revid) for revid in self._revids )
                key = '%s:revs' % self._pageid
                self._maker.add(key.encode(self.encoding), revs.encode(self.encoding))
            self._revids = []
            self._pageid = pageid
        if self._maker is not None:
            if self._pageid is None or self.maxsize <= self._maker.get_size():
                self._maker.finish()
                self._maker = None
        if self._maker is None:
            if self._pageid is not None:
                path = (self.pathpat % {'index':self._index})
                self._maker = CDBMaker(path)
                self._index += 1
        return

    def _add_data(self, key, value):
        data = compress(key, value.encode(self.encoding))
        self._maker.add(key.encode(self.encoding), data)
        return

    def close(self):
        self._new_page(None)
        return

    def add_page(self, pageid, title):
        self._new_page(pageid)
        key = '%s:title' % pageid
        self._maker.add(key.encode(self.encoding), title.encode(self.encoding))
        return

    def add_revid(self, pageid, revid):
        assert self._pageid == pageid
        self._revids.append(revid)
        return

    def add_wiki(self, pageid, revid, wiki):
        assert revid in self._revids
        key = '%s/%s:wiki' % (pageid, revid)
        key += self.ext
        self._add_data(key, wiki)
        return

    def add_text(self, pageid, revid, wiki):
        assert revid in self._revids
        key = '%s/%s:text' % (pageid, revid)
        key += self.ext
        self._add_data(key, wiki)
        return


##  WikiFileWriter
##
class WikiFileWriter(object):

    def __init__(self, output=None, pathpat=None,
                 encoding='utf-8', titleline=False, mode='page'):
        assert output is not None or pathpat is not None
        self.pathpat = pathpat
        self.encoding = encoding
        self.titleline = titleline
        self.mode = mode
        self._fp = None
        if output is not None:
            (_,self._fp) = getfp(output, mode='w', encoding=self.encoding)
        self._pageid = None
        self._title = None
        self._revid = None
        return

    def close(self):
        if self._fp is not None:
            self._fp.close()
        return

    def add_page(self, pageid, title):
        self._pageid = pageid
        self._title = title
        return

    def add_revid(self, pageid, revid):
        assert self._pageid == pageid
        self._revid = revid
        return

    def add_data(self, pageid, revid, data):
        assert self._pageid == pageid
        assert self._title is not None
        assert self._revid == revid
        if self.pathpat is not None:
            if self._fp is not None:
                self._fp.close()
            name = self._title.encode('quopri_codec')
            path = (self.pathpat % {'name':name, 'pageid':pageid})
            (_,self._fp) = getfp(path, 'w', encoding=self.encoding)
        assert self._fp is not None
        if self.mode == 'page':
            if self.titleline:
                self._fp.write(self._title+'\n')
            self._fp.write(data)
            self._fp.write('\n\f')
        else:
            self._fp.write(self._title+'\t')
            self._fp.write(data+'\n')
        return

    add_wiki = add_data
    add_text = add_data


# main
def main(argv):
    args = argv[1:]
    for path in args:
        reader = WikiDBReader(path)
        for (pageid,title) in reader:
            print(pageid, title)
            (_,revids) = reader[pageid]
            for revid in revids:
                wiki = reader.get_wiki(pageid, revid)
                print(wiki)
            print()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
