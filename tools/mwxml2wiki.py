#!/usr/bin/env python
#
# usage:
#  $ mwdump2wiki.py -n10 -t 'article%(pageid)08d.txt' jawiki.xml.bz2
#
import sys
from pymwp.utils import getfp
from pymwp.mwcdb import WikiDBWriter
from pymwp.mwcdb import WikiFileWriter
from pymwp.mwxmldump import MWXMLDumpFilter


##  MWXMLDump2DB
##
class MWXMLDump2DB(MWXMLDumpFilter):

    def __init__(self, writer):
        MWXMLDumpFilter.__init__(self)
        self.writer = writer
        return

    def close(self):
        MWXMLDumpFilter.close(self)
        self.writer.close()
        return

    def start_page(self, pageid, title):
        MWXMLDumpFilter.start_page(self, pageid, title)
        pageid = int(pageid)
        self.writer.add_page(pageid, title)
        return

    def open_file(self, pageid, title, revid, timestamp):
        print >>sys.stderr, (pageid, title, revid)
        pageid = int(pageid)
        revid = int(pageid)
        self.writer.add_revid(pageid, revid)
        return self._Stream(pageid, revid)

    def close_file(self, fp):
        self.writer.add_wiki(fp.pageid, fp.revid, ''.join(fp.text))
        return

    def write_file(self, fp, text):
        fp.text.append(text)
        return

    class _Stream(object):
        def __init__(self, pageid, revid):
            self.pageid = pageid
            self.revid = revid
            self.text = []
            return
            

# main
def main(argv):
    import getopt
    def usage():
        print ('usage: %s [-o output] [-t pathpat] [-c codec] [-T] [-Z] '
               '[file ...]' % argv[0])
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'o:t:c:TZ')
    except getopt.GetoptError:
        return usage()
    args = args or ['-']
    output = '-'
    codec = 'utf-8'
    ext = ''
    pathpat = None
    titleline = False
    for (k, v) in opts:
        if k == '-o': output = v
        elif k == '-t': pathpat = v
        elif k == '-c': codec = v 
        elif k == '-T': titleline = True
        elif k == '-Z': ext = '.gz'
    if output.endswith('.cdb'):
        writer = WikiDBWriter(output, codec=codec, ext=ext)
    else:
        writer = WikiFileWriter(
            output=output, pathpat=pathpat,
            codec=codec, titleline=titleline)
    parser = MWXMLDump2DB(writer)
    for path in args:
        (_,fp) = getfp(path)
        try:
            parser.feed_file(fp)
        finally:
            fp.close()
            parser.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
