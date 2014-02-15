PyMWP
=====

PyMWP (Python MediaWiki Parser) is a simple and robust parser 
for MediaWiki contents. It is suitable for analyzing or extracting
information from Wikipedia articles.

How to Install
--------------

  * Requires Python 2.4 or newer. (Python 3 is not supported.)
  * Download and unpack the source code.
  * Run `setup.py` to install:

    $ python setup.py install

How to Use
----------

**mwxml2wiki.py**

Converts MediaWiki XML dump files into separate text files or CDB.

Examples

    $ mwxml2wiki.py -o all.wiki.gz enwiki-20140102-pages-articles.xml.bz2

    $ mwxml2wiki.py -Z -o enwiki.wiki.cdb enwiki-20140102-pages-articles.xml.bz2

    $ mwxml2wiki.py -P 'article%(pageid)08d.wiki' enwiki-20140102-pages-articles.xml.bz2

Options

  -o filename
    Specifies the output file name.
    Supported ending suffixes: .gz, .bz2, .cdb

  -P pattern
    Output filename pattern.

  -Z
    Gzip each record in cdb fiile.

**mwwiki2txt.py**

Removes MediaWiki markup from wiki/CDB to text/CDB.

Examples

    $ mwwiki2txt.py article12.wiki > article12.txt

    $ mwwiki2txt.py -L article12.wiki > article12.link

    $ mwwiki2txt.py -Z -o jawiki.txt.cdb jawiki-20140107-pages-articles.xml.bz2

    $ mwwiki2txt.py -Z -o enwiki.txt.cdb enwiki.wiki.cdb

    $ mwwiki2txt.py -o all.txt.bz2 jawiki-20140107-pages-articles.xml.bz2

    $ mwwiki2txt.py -P 'article%(pageid)08d.txt' jawiki-20140107-pages-articles.xml.bz2

Options

  -o filename
    Specifies the output file name.
    Supported ending suffixes: .gz, .bz2, .cdb

  -P pattern
    Output filename pattern.

  -Z
    Gzip each record in cdb fiile.

  -L
    Extract keywords and links instead of text.


TODO
----

 * PEP-8 and PEP-257 conformance.
 * Better documentation.
 * More robust syntax recovery.

Terms and Conditions
--------------------

(This is so-called MIT/X License)

Copyright (c) 2011-2013 Yusuke Shinyama <yusuke at cs dot nyu dot edu>

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
