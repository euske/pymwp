#!/usr/bin/env python2
#
# usage:
#  $ mwdump2wiki.py -n10 -t 'article%(pageid)08d.txt' jawiki.xml.bz2
#
import sys
from gzip import GzipFile
from bz2 import BZ2File
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from pymwp.pycdb import CDBMaker
from pymwp.mwxmldump import MWXMLDumpFilter


##  MWXMLDump2File
##
class MWXMLDump2File(MWXMLDumpFilter):

    def __init__(self, outfp=None, template=None,
                 codec='utf-8', gzip=False, titleline=False):
        MWXMLDumpFilter.__init__(self)
        self.outfp = outfp
        self.template = template
        self.codec = codec
        self.gzip = gzip
        self.titleline = titleline
        return

    def open_file(self, pageid, title, revid, timestamp):
        print >>sys.stderr, (pageid, title, revid)
        if self.template is not None:
            name = title.encode('utf-8').encode('quopri_codec')
            path = (self.template % {'name':name, 'pageid':int(pageid), 'revid':int(revid)})
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
        if fp is not self.outfp:
            fp.close()
        return

    def write_file(self, fp, text):
        fp.write(text.encode(self.codec, 'ignore'))
        return


##  MWXMLDump2CDB
##
class MWXMLDump2CDB(MWXMLDumpFilter):

    def __init__(self, path):
        MWXMLDumpFilter.__init__(self)
        self._maker = CDBMaker(path)
        self._key = self._value = None
        return

    def close(self):
        MWXMLDumpFilter.close(self)
        self._maker.finish()
        return

    def start_page(self, pageid, title):
        MWXMLDumpFilter.start_page(self, pageid, title)
        self._maker.add('%s:title' % pageid, title.encode('utf-8'))
        self._revs = []
        return

    def start_revision(self, pageid, title, revid, timestamp):
        MWXMLDumpFilter.start_revision(self, pageid, title, revid, timestamp)
        self._revs.append(revid)
        return

    def end_page(self, pageid, title):
        MWXMLDumpFilter.end_page(self, pageid, title)
        revs = ' '.join( str(revid) for revid in self._revs )
        self._maker.add('%s:revs' % pageid, revs)
        return
    
    def open_file(self, pageid, title, revid, timestamp):
        print >>sys.stderr, (pageid, title, revid)
        self._key = '%s/%s:text' % (pageid, revid)
        self._value = StringIO()
        return GzipFile(mode='w', fileobj=self._value)

    def close_file(self, fp):
        fp.close()
        self._maker.add(self._key, self._value.getvalue())
        self._key = self._value = None
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
        print ('usage: %s [-o output] [-t template] [-c codec] [-T] [-Z] [file ...]') % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'o:t:c:TZ')
    except getopt.GetoptError:
        return usage()
    output = '-'
    codec = 'utf-8'
    template = None
    gzip = False
    titleline = False
    for (k, v) in opts:
        if k == '-o': output = v
        elif k == '-t': template = v
        elif k == '-c': codec = v 
        elif k == '-T': titleline = True
        elif k == '-Z': gzip = True
    if output.endswith('.cdb'):
        parser = MWXMLDump2CDB(output)
    else:
        parser = MWXMLDump2File(
            outfp=getfp(output, mode='w'), template=template,
            codec=codec, gzip=gzip, titleline=titleline)
    for path in (args or ['-']):
        fp = getfp(path)
        try:
            parser.feed_file(fp)
        finally:
            fp.close()
            parser.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
