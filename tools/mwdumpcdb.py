#!/usr/bin/env python2
import re
import sys
from gzip import GzipFile
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from pymwp.pycdb import CDBReader


##  MWCDB2Dumper
##
class MWCDB2Dumper(object):

    def __init__(self, path):
        self.reader = CDBReader(path)
        return

    def __iter__(self):
        for key in self.reader:
            try:
                i = key.rindex('/')
                pageid = int(key[:i])
                revision = int(key[i+1:])
            except ValueError:
                continue
            yield self.get(pageid, revision)
        return

    def get(self, pageid, revision=0):
        try:
            title = self.reader['%d:title' % pageid].decode('utf-8')
        except KeyError:
            title = None
        key = '%d/%d' % (pageid, revision)
        buf = StringIO(self.reader[key])
        fp = GzipFile(mode='r', fileobj=buf)
        text = fp.read().decode('utf-8')
        return (title, text)


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
        print ('usage: %s [-c codec] [-o output] [-T] [cdbfile] [key ...]') % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'o:c:T')
    except getopt.GetoptError:
        return usage()
    output = None
    codec = 'utf-8'
    titleline = False
    for (k, v) in opts:
        if k == '-o': output = v
        elif k == '-c': codec = v
        elif k == '-T': titleline = True
    if not args: return usage()
    outfp = getfp(output or '-', 'w')
    reader = MWCDB2Dumper(args.pop(0))
    def dump(fp, title, text):
        if titleline:
            fp.write(title.encode(codec, 'ignore')+'\n')
        fp.write(text.encode(codec, 'ignore'))
        return
    if args:
        for pageid in args:
            (title, text) = reader.get(int(pageid))
            dump(outfp, title, text)
    else:
        for (title,text) in reader:
            dump(outfp, title, text)
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
