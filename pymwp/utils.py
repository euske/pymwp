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
    else:
        return (path, open(path, mode=mode, encoding=encoding))
