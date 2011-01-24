#!/usr/bin/env python2
#
# usage:
#  ./tools/mwdump2wiki.py -n10 -t 'article%(pageid)05d.txt' dev/jawiki.xml.bz2
#
import re
import sys
from pymwp.mwxmldump import MWXMLDumpSplitter


##  MWDump2Wiki
##
class MWDump2Wiki(MWXMLDumpSplitter):

    def __init__(self, output=sys.stdout, template=None,
                 titlepat=None, pageids=None,
                 revisionlimit=1, codec='utf-8',
                 titleline=False):
        MWXMLDumpSplitter.__init__(
            self, output=output, template=template,
            titlepat=titlepat, pageids=pageids,
            revisionlimit=revisionlimit, codec=codec)
        self.titleline = titleline
        return

    def start_revision(self, pageid, title, revision):
        MWXMLDumpSplitter.start_revision(self, pageid, title, revision)
        if self.titleline:
            self.write(title+'\n')
        return


# main
def main(argv):
    import getopt
    def usage():
        print ('usage: %s [-c codec] [-t template] [-e titlepat] [-n npages] '
               '[-p pageids] [-r revisionlimit] [-T)itleline] [file ...]') % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'c:t:e:n:p:r:T')
    except getopt.GetoptError:
        return usage()
    codec = 'utf-8'
    template = None
    titlepat = None
    pageids = None
    revisionlimit = 1
    titleline = False
    for (k, v) in opts:
        if k == '-c': codec = v 
        elif k == '-t': template = v
        elif k == '-e': titlepat = re.compile(v)
        elif k == '-n':
            pageids = set(xrange(int(v)))
        elif k == '-p':
            if pageids is None:
                pageids = set()
            for x in v.split(','):
                pageids.add(int(x))
        elif k == '-r': revisionlimit = int(v)
        elif k == '-T': titleline = True
    for path in (args or ['-']):
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
        parser = MWDump2Wiki(
            codec=codec, template=template,
            titlepat=titlepat, pageids=pageids,
            revisionlimit=revisionlimit,
            titleline=titleline)
        parser.feed_file(fp)
        fp.close()
        parser.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
