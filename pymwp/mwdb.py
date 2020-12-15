#!/usr/bin/env python
import sys
import sqlite3
import io
import gzip
from .utils import getfp


##  WikiDB
##
class WikiDB:

    def __init__(self, path, gzipped=False):
        self.gzipped = gzipped
        self._conn = sqlite3.connect(path)
        self._conn.executescript('''
CREATE TABLE IF NOT EXISTS MWPage (
    PageId INTEGER PRIMARY KEY,
    Title TEXT
);
CREATE INDEX IF NOT EXISTS MWPageTitleIndex ON MWPage(Title);

CREATE TABLE IF NOT EXISTS MWRevision (
    RevId INTEGER PRIMARY KEY,
    PageId INTEGER NOT NULL,
    Timestamp TEXT,
    Content BLOB
);
CREATE INDEX IF NOT EXISTS MWRevisionPageIdIndex ON MWRevision(PageId);
''')
        return

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()
        return

    def close(self):
        self._conn.commit()
        self._conn.close()
        return

    def __iter__(self):
        return self.get_pageids()

    def __getitem__(self, pageid):
        return self.get_revids(pageid)

    def get_pageids(self):
        cur = self._conn.cursor()
        for (pageid,title) in cur.execute('SELECT PageId,Title FROM MWPage;'):
            yield (pageid, title)
        return

    def get_revids(self, pageid):
        cur = self._conn.cursor()
        for (revid,timestamp) in cur.execute(
                'SELECT RevId,Timestamp FROM MWRevision WHERE PageId = ?;',
                (pageid,)):
            yield (revid, timestamp)
        return

    def get_content(self, revid):
        cur = self._conn.cursor()
        for (timestamp, content) in cur.execute(
                'SELECT Content FROM MWRevision WHERE RevId = ?;',
                (revid,)):
            if self.gzipped:
                buf = io.BytesIO(content)
                fp = gzip.GzipFile(mode='r', fileobj=buf)
                content = fp.read().decode('utf-8')
            return content
        raise KeyError(revid)

    def add_page(self, pageid, title):
        self._conn.execute('INSERT INTO MWPage VALUES (?,?);',
                           (pageid, title))
        return

    def add_content(self, pageid, revid, timestamp, content):
        if self.gzipped:
            buf = io.BytesIO()
            fp = gzip.GzipFile(mode='w', fileobj=buf)
            fp.write(content.encode('utf-8'))
            fp.close()
            content = buf.getvalue()
        self._conn.execute('INSERT INTO MWRevision VALUES (?,?,?,?);',
                           (revid, pageid, timestamp, content))
        return


##  WikiFileWriter
##
class WikiFileWriter:

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
        return

    def close(self):
        if self._fp is not None:
            self._fp.close()
        return

    def add_page(self, pageid, title):
        self._pageid = pageid
        self._title = title
        return

    def add_content(self, pageid, revid, timestamp, content):
        assert self._pageid == pageid
        assert self._title is not None
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
            self._fp.write(content)
            self._fp.write('\n\f')
        else:
            self._fp.write(self._title+'\t')
            self._fp.write(content+'\n')
        return


# main
def main(argv):
    args = argv[1:]
    for path in args:
        reader = WikiDB(path)
        for (pageid,title) in reader:
            print(pageid, title)
            (_,revids) = reader[pageid]
            for revid in revids:
                data = reader.get_content(revid)
                print(data)
            print()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
