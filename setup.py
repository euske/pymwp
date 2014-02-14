#!/usr/bin/env python
from distutils.core import setup
from pymwp import __version__

setup(
    name='pymwp',
    version=__version__,
    description='Python MediaWiki parser',
    long_description=
    '''PyMWP is a simple and robust parser for MediaWiki contents.
It is suitable for analyzing or extracting information
from Wikipedia articles.''',
    license='MIT/X',
    author='Yusuke Shinyama',
    author_email='yusuke at cs dot nyu dot edu',
    url='https://github.com/euske/pymwp',
    packages=[
        'pymwp',
    ],
    scripts=[
        'tools/mwdumpcdb.py',
        'tools/mwxml2age.py',
        'tools/mwxml2wiki.py',
        'tools/mwwiki2txt.py',
    ],
    keywords=[
        'mediawiki parser',
        'text mining'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Topic :: Text Processing',
    ],
)
