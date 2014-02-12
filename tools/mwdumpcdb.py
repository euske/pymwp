#!/usr/bin/env python
import sys
from pymwp.utils import getfp
from pymwp.mwcdb import WikiDBReader

# main
def main(argv):
    import getopt
    def usage():
        print ('usage: %s {-t|-w} [-c codec] [-o output] [-T] [cdbfile] [key ...]') % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'two:c:T')
    except getopt.GetoptError:
        return usage()
    text = True
    output = None
    codec = 'utf-8'
    titleline = False
    for (k, v) in opts:
        if k == '-o': output = v
        elif k == '-c': codec = v
        elif k == '-T': titleline = True
        elif k == '-t': text = True
        elif k == '-w': text = False
    if not args: return usage()
    outfp = getfp(output or '-', 'w')
    reader = WikiDBReader(args.pop(0))
    if args:
        pageids = [ int(pageid) for pageid in args ]
    else:
        pageids = ( pageid for (pageid,_) in reader )
    for pageid in pageids:
        (title,revids) = reader[pageid]
        if titleline:
            outfp.write(title.encode(codec, 'ignore')+'\n')
        for revid in revids:
            if text:
                data = reader.get_text(pageid, revid)
            else:
                data = reader.get_wiki(pageid, revid)
            outfp.write(data.encode(codec, 'ignore'))
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
