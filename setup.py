#!/usr/bin/env python2
from distutils.core import setup
from pymwp import __version__

setup(
    name='pymwp',
    version=__version__,
    description='MediaWiki parser',
    long_description='''MediaWiki parser''',
    license='MIT/X',
    author='Yusuke Shinyama',
    author_email='yusuke at cs dot nyu dot edu',
    url='http://www.unixuser.org/~euske/python/pymwp/index.html',
    packages=[
    'pymwp',
    ],
    scripts=[
    'tools/mwdump2wiki.py',
    'tools/mwwiki2txt.py',
    ],
    keywords=['mediawiki parser', 'text mining'],
    classifiers=[
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: MIT License',
    'Topic :: Text Processing',
    ],
    )
