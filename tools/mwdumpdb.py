#!/usr/bin/env python
#
# Usage examples:
#  $ mwdumpdb.py -Z jawiki.txt.db 19 23 346 9287
#  $ mwdumpdb.py -Z jawiki.wiki.db
#  $ mwdumpdb.py -Z -o all.txt.gz jawiki.txt.db
#
import sys
import os.path
from pymwp.utils import getfp
from pymwp.mwdb import WikiDB

# main
def main(argv):
    import getopt
    def usage():
        print ('usage: %s [-c encoding] [-o output] [-T] [-Z] '
               'dbfile [pageid ...]' % argv[0])
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'o:c:TZ')
    except getopt.GetoptError:
        return usage()
    output = '-'
    encoding = 'utf-8'
    titleline = False
    gzipped = False
    for (k, v) in opts:
        if k == '-o': output = v
        elif k == '-c': encoding = v
        elif k == '-T': titleline = True
        elif k == '-Z': gzipped = True
    if not args: return usage()
    (_,outfp) = getfp(output, 'w', encoding=encoding)
    readers = []
    pageids = []
    for arg in args:
        if os.path.isfile(arg):
            readers.append(WikiDB(arg, gzipped=gzipped))
        else:
            pageids.append(arg)
    for reader in readers:
        for (pageid,title) in (pageids or iter(reader)):
            try:
                revids = reader[pageid]
            except KeyError:
                continue
            if titleline:
                outfp.write(title+'\n')
            for (revid,timestamp) in revids:
                try:
                    data = reader.get_content(revid)
                except KeyError:
                    continue
                outfp.write(data)
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
