#!/usr/bin/env python2
#
# usage:
#  $ mwdump2wiki.py -n10 -t 'article%(pageid)05d.txt' jawiki.xml.bz2
#
import re
import sys
from gzip import GzipFile
from bz2 import BZ2File
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from pymwp.pycdb import cdbmake
from pymwp.mwxmldump import MWXMLDumpFilter


##  MWDump2File
##
class MWDump2File(MWXMLDumpFilter):

    def __init__(self, output=sys.stdout, template=None,
                 codec='utf-8', gzip=False, titleline=False,
                 titlepat=None, revisionlimit=1):
        MWXMLDumpFilter.__init__(
            self, titlepat=titlepat, 
            revisionlimit=revisionlimit)
        self.gzip = gzip
        self.codec = codec
        self.output = output
        self.template = template
        self.titleline = titleline
        return

    def open_file(self, pageid, title, revision):
        if self.template is not None:
            name = title.encode('utf-8').encode('quopri_codec')
            path = (self.template % {'name':name, 'pageid':pageid, 'revision':revision})
            if self.gzip:
                fp = GzipFile(path, 'w')
            else:
                fp = open(path, 'w')
        else:
            fp = self.output
        if self.titleline:
            fp.write(title+'\n')
        return fp

    def close_file(self, fp):
        if self.template is not None:
            fp.close()
        return

    def write_file(self, fp, text):
        fp.write(text.encode(self.codec, 'ignore'))
        return
            

##  MWDump2CDB
##
class MWDump2CDB(MWXMLDumpFilter):

    def __init__(self, path,
                 titlepat=None, revisionlimit=1):
        MWXMLDumpFilter.__init__(
            self, titlepat=titlepat, 
            revisionlimit=revisionlimit)
        self._maker = cdbmake(path, path+'.tmp')
        self._key = None
        return

    def close(self):
        MWXMLDumpFilter.close(self)
        self._maker.finish()
        return

    def open_file(self, pageid, title, revision):
        self._key = '%s:%d' % (title.encode('utf-8'), revision)
        buf = StringIO()
        fp = GzipFile(mode='w', fileobj=buf)
        fp.buf = buf
        return fp

    def close_file(self, fp):
        fp.close()
        self._maker.add(self._key, fp.buf.getvalue())
        self._key = None
        return

    def write_file(self, fp, text):
        fp.write(text.encode('utf-8'))
        return
            

# main
def main(argv):
    import getopt
    def usage():
        print ('usage: %s [-C cdbpath] [-t template] [-c codec] [-T] [-Z] '
               '[-e titlepat] [-r revisionlimit] [file ...]') % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'C:t:c:TZe:r:')
    except getopt.GetoptError:
        return usage()
    cdbpath = None
    codec = 'utf-8'
    template = None
    titlepat = None
    revisionlimit = 1
    gzip = False
    titleline = False
    for (k, v) in opts:
        if k == '-C': cdbpath = v
        elif k == '-t': template = v
        elif k == '-c': codec = v 
        elif k == '-T': titleline = True
        elif k == '-Z': gzip = True
        elif k == '-e': titlepat = re.compile(v)
        elif k == '-r': revisionlimit = int(v)
    if cdbpath is not None:
        parser = MWDump2CDB(
            cdbpath, 
            titlepat=titlepat, 
            revisionlimit=revisionlimit)
    else:
        parser = MWDump2File(
            template=template, codec=codec, titleline=titleline, gzip=gzip,
            titlepat=titlepat, 
            revisionlimit=revisionlimit)
    for path in (args or ['-']):
        if path == '-':
            fp = sys.stdin
        elif path.endswith('.gz'):
            fp = GzipFile(path)
        elif path.endswith('.bz2'):
            fp = BZ2File(path)
        else:
            fp = open(path)
        try:
            parser.feed_file(fp)
        finally:
            fp.close()
            parser.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
