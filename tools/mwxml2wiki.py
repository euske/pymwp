#!/usr/bin/env python
#
# Usage examples:
#  $ mwxml2wiki.py -o all.wiki.gz jawiki.xml.bz2
#  $ mwxml2wiki.py -Z -o jawiki.wiki.cdb jawiki.xml.bz2
#  $ mwxml2wiki.py -P 'article%(pageid)08d.wiki' jawiki.xml.bz2
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
        print(pageid, title, revid, file=sys.stderr)
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
        print ('usage: %s [-o output] [-P pathpat] [-c encoding] [-T] [-Z] '
               '[file ...]' % argv[0])
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'o:P:c:TZ')
    except getopt.GetoptError:
        return usage()
    args = args or ['-']
    output = '-'
    encoding = 'utf-8'
    ext = ''
    pathpat = None
    titleline = False
    for (k, v) in opts:
        if k == '-o': output = v
        elif k == '-P': pathpat = v
        elif k == '-c': encoding = v
        elif k == '-T': titleline = True
        elif k == '-Z': ext = '.gz'
    if output.endswith('.cdb'):
        writer = WikiDBWriter(output, encoding=encoding, ext=ext)
    else:
        writer = WikiFileWriter(
            output=output, pathpat=pathpat,
            encoding=encoding, titleline=titleline)
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
