#!/usr/bin/env python
#
# usage:
#  $ mwdump2wiki.py -n10 -t 'article%(pageid)08d.txt' jawiki.xml.bz2
#
import sys
from pymwp.utils import getfp
from pymwp.mwcdb import WikiDBWriter
from pymwp.mwxmldump import MWXMLDumpFilter


##  MWXMLDump2File
##
class MWXMLDump2File(MWXMLDumpFilter):

    def __init__(self, outfp=None, template=None,
                 codec='utf-8', titleline=False):
        MWXMLDumpFilter.__init__(self)
        assert outfp is not None or template is not None
        self.outfp = outfp
        self.template = template
        self.codec = codec
        self.titleline = titleline
        return

    def open_file(self, pageid, title, revid, timestamp):
        print >>sys.stderr, (pageid, title, revid)
        if self.template is not None:
            name = title.encode('utf-8').encode('quopri_codec')
            path = (self.template % {'name':name, 'pageid':int(pageid), 'revid':int(revid)})
            (_,fp) = getfp(path, 'w')
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
        self.writer.add_page(pageid, title)
        return

    def open_file(self, pageid, title, revid, timestamp):
        print >>sys.stderr, (pageid, title, revid)
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
        print ('usage: %s [-o output] [-t template] [-c codec] [-T] [file ...]') % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'o:t:c:T')
    except getopt.GetoptError:
        return usage()
    args = args or ['-']
    output = '-'
    codec = 'utf-8'
    outfp = None
    template = None
    titleline = False
    for (k, v) in opts:
        if k == '-o': output = v
        elif k == '-t': template = v
        elif k == '-c': codec = v 
        elif k == '-T': titleline = True
    if output.endswith('.cdb'):
        writer = WikiDBWriter(output)
        parser = MWXMLDump2CDB(writer)
    else:
        if template is None:
            (_,outfp) = getfp(output, mode='w')
        parser = MWXMLDump2File(
            outfp=outfp, template=template,
            codec=codec, titleline=titleline)
    for path in args:
        (_,fp) = getfp(path)
        try:
            parser.feed_file(fp)
        finally:
            fp.close()
            parser.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
