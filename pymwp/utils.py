#!/usr/bin/env python
import sys
import gzip
import bz2
from io import BytesIO

def getfp(path, mode='r', encoding='utf-8'):
    if path == '-' and mode == 'r':
        return (path, sys.stdin)
    elif path == '-' and mode == 'w':
        return (path, sys.stdout)
    elif path.endswith('.gz'):
        return (path[:-3], gzip.open(path, mode=mode+'t', encoding=encoding))
    elif path.endswith('.bz2'):
        return (path[:-4], bz2.open(path, mode=mode+'t', encoding=encoding))
    elif path.endswith('.7z'):
        import py7zr
        return (path[:-4], py7zr.open(path, mode=mode+'t', encoding=encoding))
    else:
        return (path, open(path, mode=mode, encoding=encoding))

def compress(name, data):
    if name.endswith('.gz'):
        buf = BytesIO()
        fp = gzip.GzipFile(mode='w', fileobj=buf)
        fp.write(data)
        fp.close()
        data = buf.getvalue()
    elif name.endswith('.bz2'):
        buf = BytesIO()
        fp = bz2.BZ2File(mode='w', fileobj=buf)
        fp.write(data)
        fp.close()
        data = buf.getvalue()
    return data

def decompress(name, data):
    if name.endswith('.gz'):
        buf = BytesIO(data)
        fp = gzip.GzipFile(mode='r', fileobj=buf)
        data = fp.read()
    elif name.endswith('.bz2'):
        buf = BytesIO(data)
        fp = bz2.BZ2File(mode='r', fileobj=buf)
        data = fp.read()
    return data
