#!/usr/bin/env python
#
# Usage examples:
#  $ mwdump2age.py jawiki.xml.bz2 > jawiki.txt
#
import sys
import time
from pymwp.utils import getfp
from pymwp.mwxmldump import MWXMLDumpParser


##  WikiAgeExtractor
class WikiAgeExtractor(MWXMLDumpParser):

    def __init__(self, current):
        MWXMLDumpParser.__init__(self)
        self.current = current
        return

    def start_page(self, pageid, title):
        self._timestamps = []
        return

    def end_page(self, pageid, title):
        days = [ int(dt/86400) for dt in self._timestamps ]
        print(pageid, ' '.join(map(str, days)))
        return

    def start_revision(self, pageid, title, revid, timestamp):
        t = time.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
        self._timestamps.append(self.current - time.mktime(t))
        return

# main
def main(argv):
    args = argv[1:] or ['-']
    for path in args:
        print(path, file=sys.stderr)
        (_,fp) = getfp(path)
        parser = WikiAgeExtractor(time.time())
        parser.feed_file(fp)
        parser.close()
        fp.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
