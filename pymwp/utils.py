#!/usr/bin/env python
import sys
from gzip import GzipFile
from bz2 import BZ2File
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

def getfp(path, mode='r'):
    if path == '-' and mode == 'r':
        return (path, sys.stdin)
    elif path == '-' and mode == 'w':
        return (path, sys.stdout)
    elif path.endswith('.gz'):
        return (path[:-3], GzipFile(path, mode=mode))
    elif path.endswith('.bz2'):
        return (path[:-4], BZ2File(path, mode=mode))
    else:
        return (path, open(path, mode=mode+'b'))

def compress(name, data):
    if name.endswith('.gz'):
        buf = StringIO()
        fp = GzipFile(mode='w', fileobj=buf)
        fp.write(data)
        fp.close()
        data = buf.getvalue()
    elif name.endswith('.bz2'):
        buf = StringIO()
        fp = BZ2File(mode='w', fileobj=buf)
        fp.write(data)
        fp.close()
        data = buf.getvalue()
    return data

def decompress(name, data):
    if name.endswith('.gz'):
        buf = StringIO(data)
        fp = GzipFile(mode='r', fileobj=buf)
        data = fp.read()
    elif name.endswith('.bz2'):
        buf = StringIO(data)
        fp = BZ2File(mode='r', fileobj=buf)
        data = fp.read()
    return data
