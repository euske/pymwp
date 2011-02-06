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
from pymwp.pycdb import CDBMaker
from pymwp.mwxmldump import MWXMLDumpFilter


##  MWDump2File
##
class MWDump2File(MWXMLDumpFilter):

    def __init__(self, outfp=sys.stdout, template=None,
                 codec='utf-8', gzip=False, titleline=False,
                 titlepat=None, revisionlimit=1):
        MWXMLDumpFilter.__init__(
            self, titlepat=titlepat, 
            revisionlimit=revisionlimit)
        self.gzip = gzip
        self.codec = codec
        self.outfp = outfp
        self.template = template
        self.titleline = titleline
        return

    def open_file(self, pageid, title, revision):
        print >>sys.stderr, (pageid, title, revision)
        if self.template is not None:
            name = title.encode('utf-8').encode('quopri_codec')
            path = (self.template % {'name':name, 'pageid':pageid, 'revision':revision})
            if self.gzip:
                fp = GzipFile(path, 'w')
            else:
                fp = open(path, 'w')
        else:
            fp = self.outfp
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
        self._maker = CDBMaker(path)
        self._key = None
        return

    def close(self):
        MWXMLDumpFilter.close(self)
        self._maker.finish()
        return

    def start_page(self, pageid, title):
        self._maker.add('%d:title' % pageid, title.encode('utf-8'))
        return
    
    def open_file(self, pageid, title, revision):
        print >>sys.stderr, (pageid, title, revision)
        self._key = '%d/%d' % (pageid,  revision)
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
    def getfp(path, mode='r'):
        if path == '-' and mode == 'r':
            return sys.stdin
        elif path == '-' and mode == 'w':
            return sys.stdout
        elif path.endswith('.gz'):
            return GzipFile(path, mode=mode)
        elif path.endswith('.bz2'):
            return BZ2File(path, mode=mode)
        else:
            return open(path, mode=mode+'b')
    def usage():
        print ('usage: %s [-o output] [-t template] [-c codec] [-T] [-Z] '
               '[-e titlepat] [-r revisionlimit] [file ...]') % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'o:t:c:TZe:r:')
    except getopt.GetoptError:
        return usage()
    output = '-'
    codec = 'utf-8'
    template = None
    titlepat = None
    revisionlimit = 1
    gzip = False
    titleline = False
    for (k, v) in opts:
        if k == '-o': output = v
        elif k == '-t': template = v
        elif k == '-c': codec = v 
        elif k == '-T': titleline = True
        elif k == '-Z': gzip = True
        elif k == '-e': titlepat = re.compile(v)
        elif k == '-r': revisionlimit = int(v)
    if output.endswith('.cdb'):
        parser = MWDump2CDB(
            output, 
            titlepat=titlepat, 
            revisionlimit=revisionlimit)
    else:
        parser = MWDump2File(
            outfp=getfp(output, mode='w'),
            template=template, codec=codec, titleline=titleline, gzip=gzip,
            titlepat=titlepat, 
            revisionlimit=revisionlimit)
    for path in (args or ['-']):
        fp = getfp(path)
        try:
            parser.feed_file(fp)
        finally:
            fp.close()
            parser.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
