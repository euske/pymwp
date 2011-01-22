#!/usr/bin/env python2
import sys
from mwtokenizer import WikiToken
from mwtokenizer import WikiHeadlineToken
from mwtokenizer import WikiItemizeToken
from mwtokenizer import XMLTagToken
from mwtokenizer import XMLStartTagToken
from mwtokenizer import XMLEndTagToken
from mwtokenizer import WikiTextTokenizer


##  WikiTree
##
class WikiTree(object):

    NAME = None

    def __init__(self):
        self.name = self.NAME
        self._subtree = []
        return

    def __repr__(self):
        return ('<%s %s>' %
                (self.__class__.__name__,
                 ' '.join(map(repr, self._subtree))))

    def __iter__(self):
        return iter(self._subtree)

    def get_text(self):
        s = u''
        for x in self:
            if isinstance(x, WikiTree):
                s += x.get_text()
            elif isinstance(x, basestring):
                s += x
        return s

    def append(self, t):
        if (self._subtree and
            isinstance(t, basestring) and
            isinstance(self._subtree[-1], basestring)):
            assert type(t) is type(self._subtree[-1]), (t, self._subtree[-1])
            self._subtree[-1] += t
        else:
            self._subtree.append(t)
        return

    def add_arg(self):
        tree = WikiArgTree()
        self.append(tree)
        return tree
    
    def finish(self):
        return

class WikiTokenTree(WikiTree):

    def __init__(self, token):
        WikiTree.__init__(self)
        self.token = token
        return

class WikiPageTree(WikiTree): NAME = 'page'
class WikiArgTree(WikiTree): NAME = 'arg'
class WikiCommentTree(WikiTree): NAME = 'comment'
class WikiPreTree(WikiTree): NAME = 'pre'
class WikiKeywordTree(WikiTree): NAME = 'keyword'
class WikiSpecialTree(WikiTree): NAME = 'special'
class WikiLinkTree(WikiTree): NAME = 'link'
class WikiTableTree(WikiTree): NAME = 'table'
class WikiTableCaptionTree(WikiTree): NAME = 'caption'
class WikiTableRowTree(WikiTree): NAME = 'tr'
class WikiTableHeaderTree(WikiTree): NAME = 'th'
class WikiTableDataTree(WikiTree): NAME = 'td'
class WikiXMLTree(WikiTokenTree): NAME = 'xml'
class WikiSpanTree(WikiTokenTree): NAME = 'span'
class WikiItemizeTree(WikiTokenTree): NAME = 'item'
class WikiHeadlineTree(WikiTokenTree): NAME = 'headline'


##  WikiTextParser
##
class WikiTextParser(WikiTextTokenizer):

    def __init__(self):
        WikiTextTokenizer.__init__(self)
        self._parse = self._parse_main
        self._stack = []
        self._root = self._tree = WikiPageTree()
        return

    def get_root(self):
        return self._root

    def feed_tokens(self, tokens):
        i = 0
        while 0 <= i and i < len(tokens):
            i = self._parse(i, tokens[i])
            assert i is not None
        return

    def handle_token(self, token):
        WikiTextTokenizer.handle_token(self, token)
        self.feed_tokens([token])
        return

    def handle_char(self, c):
        WikiTextTokenizer.handle_char(self, c)
        self._tree.append(c)
        return

    def invalid_token(self, token):
        return

    def _push_context(self, tree, parse):
        self._tree.append(tree)
        self._stack.append((self._parse, self._tree))
        self._tree = tree
        self._parse = parse
        return

    def _pop_context(self):
        assert self._stack
        self._tree.finish()
        (self._parse, self._tree) = self._stack.pop()
        return

    def _parse_main(self, i, t):
        if isinstance(t, XMLStartTagToken):
            if t.name.endswith('/'):
                self._tree.append(t)
            else:
                self._push_context(WikiXMLTree(t), self._parse_xml)
            return i+1
        elif t in (WikiToken.QUOTE2, WikiToken.QUOTE3, WikiToken.QUOTE5):
            self._push_context(WikiSpanTree(t), self._parse_span)
            return i+1
        elif isinstance(t, WikiItemizeToken):
            self._push_context(WikiItemizeTree(t), self._parse_itemize)
            return i+1
        elif isinstance(t, WikiHeadlineToken):
            self._push_context(WikiHeadlineTree(t), self._parse_headline)
            return i+1
        elif t is WikiToken.COMMENT_OPEN:
            self._push_context(WikiCommentTree(), self._parse_comment)
            return i+1
        elif t is WikiToken.KEYWORD_OPEN:
            self._push_context(WikiKeywordTree(), self._parse_keyword)
            return i+1
        elif t is WikiToken.LINK_OPEN:
            self._push_context(WikiLinkTree(), self._parse_link)
            return i+1
        elif t is WikiToken.SPECIAL_OPEN:
            self._push_context(WikiSpecialTree(), self._parse_special)
            return i+1
        elif t is WikiToken.TABLE_OPEN:
            self._push_context(WikiTableTree(), self._parse_table)
            return i+1
        elif t is WikiToken.PRE:
            self._push_context(WikiPreTree(), self._parse_pre)
            return i+1
        elif t in (WikiToken.BAR,
                   WikiToken.TABLE_DATA):
            self._tree.append(u'|')
            return i+1
        elif t in (WikiToken.EOL,
                   WikiToken.BLANK):
            self._tree.append(u' ')
            return i+1
        elif t in (WikiToken.HR,
                   WikiToken.PAR): 
            self._tree.append(t)
            return i+1
        elif isinstance(t, basestring):
            self._tree.append(t)
            return i+1
        else:
            self.invalid_token(t)
            return i+1

    def _parse_xml(self, i, t):
        assert isinstance(self._tree, WikiXMLTree), self._tree
        if isinstance(t, XMLEndTagToken):
            self._pop_context()
            return i+1
        else:
            return self._parse_main(i, t)

    def _parse_comment(self, i, t):
        assert isinstance(self._tree, WikiCommentTree), self._tree
        if t is WikiToken.COMMENT_CLOSE:
            self._pop_context()
            return i+1
        else:
            return self._parse_main(i, t)
        
    def _parse_keyword(self, i, t):
        assert isinstance(self._tree, WikiKeywordTree), self._tree
        if t is WikiToken.KEYWORD_CLOSE:
            self._pop_context()
            return i+1
        else:
            self._push_context(WikiArgTree(), self._parse_keyword_arg)
            return i
        
    def _parse_keyword_arg(self, i, t):
        assert isinstance(self._tree, WikiArgTree), self._tree
        if t is WikiToken.BAR:
            self._pop_context()
            return i+1
        elif t is WikiToken.KEYWORD_CLOSE:
            self._pop_context()
            return i
        else:
            return self._parse_main(i, t)
    
    def _parse_link(self, i, t):
        assert isinstance(self._tree, WikiLinkTree), self._tree
        if t is WikiToken.LINK_CLOSE:
            self._pop_context()
            return i+1
        else:
            self._push_context(WikiArgTree(), self._parse_link_arg)
            return i
    
    def _parse_link_arg(self, i, t):
        assert isinstance(self._tree, WikiArgTree), self._tree
        if t is WikiToken.BLANK:
            self._pop_context()
            return i+1
        elif t is WikiToken.LINK_CLOSE:
            self._pop_context()
            return i
        else:
            return self._parse_main(i, t)
    
    def _parse_special(self, i, t):
        assert isinstance(self._tree, WikiSpecialTree), self._tree
        if t is WikiToken.SPECIAL_CLOSE:
            self._pop_context()
            return i+1
        else:
            self._push_context(WikiArgTree(), self._parse_special_arg)
            return i

    def _parse_special_arg(self, i, t):
        assert isinstance(self._tree, WikiArgTree), self._tree
        if t is WikiToken.BAR:
            self._pop_context()
            return i+1
        elif t is WikiToken.SPECIAL_CLOSE:
            self._pop_context()
            return i
        else:
            return self._parse_main(i, t)
    
    def _parse_span(self, i, t):
        assert isinstance(self._tree, WikiSpanTree), self._tree
        if t is self._tree.token:
            self._pop_context()
            return i+1
        else:
            return self._parse_main(i, t)
        
    def _parse_pre(self, i, t):
        assert isinstance(self._tree, WikiPreTree), self._tree
        if t is WikiToken.EOL:
            self._pop_context()
            return i+1
        else:
            return self._parse_main(i, t)
        
    def _parse_table(self, i, t):
        assert isinstance(self._tree, WikiTableTree), self._tree
        if t is WikiToken.TABLE_CLOSE:
            self._pop_context()
            return i+1
        elif t is WikiToken.TABLE_CAPTION:
            self._push_context(WikiTableCaptionTree(), self._parse_table_caption)
            return i+1
        elif t is WikiToken.TABLE_ROW:
            self._push_context(WikiTableRowTree(), self._parse_table_row)
            return i+1
        elif t in (WikiToken.TABLE_ROW,
                   WikiToken.TABLE_DATA,
                   WikiToken.TABLE_HEADER): 
            self._push_context(WikiTableRowTree(), self._parse_table_row)
            return i
        else:
            return self._parse_main(i, t)
        
    def _parse_table_caption(self, i, t):
        assert isinstance(self._tree, WikiTableCaptionTree), self._tree
        if t in (WikiToken.TABLE_CLOSE,
                 WikiToken.TABLE_ROW,
                 WikiToken.TABLE_HEADER,
                 WikiToken.TABLE_DATA):
            self._pop_context()
            return i
        else:
            return self._parse_main(i, t)
        
    def _parse_table_row(self, i, t):
        assert isinstance(self._tree, WikiTableRowTree), self._tree
        if t in (WikiToken.TABLE_CLOSE,
                 WikiToken.TABLE_ROW,
                 WikiToken.TABLE_CAPTION):
            self._pop_context()
            return i
        elif t in (WikiToken.TABLE_HEADER,
                   WikiToken.TABLE_HEADER_SEP):
            self._push_context(WikiTableHeaderTree(), self._parse_table_header)
            return i+1
        elif t in (WikiToken.TABLE_DATA,
                   WikiToken.TABLE_DATA_SEP):
            self._push_context(WikiTableDataTree(), self._parse_table_data)
            return i+1
        else:
            return self._parse_main(i, t)
        
    def _parse_table_header(self, i, t):
        assert isinstance(self._tree, WikiTableHeaderTree), self._tree
        if t in (WikiToken.TABLE_CLOSE,
                 WikiToken.TABLE_ROW,
                 WikiToken.TABLE_CAPTION,
                 WikiToken.TABLE_HEADER,
                 WikiToken.TABLE_HEADER_SEP,
                 WikiToken.TABLE_DATA,
                 WikiToken.TABLE_DATA_SEP):
            self._pop_context()            
            return i
        else:
            return self._parse_main(i, t)
        
    def _parse_table_data(self, i, t):
        assert isinstance(self._tree, WikiTableDataTree), self._tree
        if t in (WikiToken.TABLE_CLOSE,
                 WikiToken.TABLE_ROW,
                 WikiToken.TABLE_CAPTION,
                 WikiToken.TABLE_HEADER,
                 WikiToken.TABLE_HEADER_SEP,
                 WikiToken.TABLE_DATA,
                 WikiToken.TABLE_DATA_SEP):
            self._pop_context()            
            return i
        else:
            return self._parse_main(i, t)
        
    def _parse_itemize(self, i, t):
        assert isinstance(self._tree, WikiItemizeTree), self._tree
        if t is WikiToken.EOL:
            self._pop_context()
            return i+1
        else:
            return self._parse_main(i, t)
        
    def _parse_headline(self, i, t):
        assert isinstance(self._tree, WikiHeadlineTree), self._tree
        if t is WikiToken.EOL:
            self._pop_context()
            return i+1
        else:
            return self._parse_main(i, t)


##  WikiTextParserTester
##
class WikiTextParserTester(WikiTextParser):
    
    def run(self, text):
        self.feed_text(text)
        self.close()
        print self.get_root()
        return f(self.get_root())


# main
def main(argv):
    args = argv[1:] or ['-']
    codec = 'utf-8'
    for path in args:
        if path == '-':
            fp = sys.stdin
        elif path.endswith('.gz'):
            from gzip import GzipFile
            fp = GzipFile(path)
        elif path.endswith('.bz2'):
            from bz2 import BZ2File
            fp = BZ2File(path)
        else:
            fp = open(path)
        parser = WikiTextParser()
        for line in fp:
            line = unicode(line, codec)
            parser.feed_text(line)
        fp.close()
        parser.close()
        def f(x, i=0):
            if isinstance(x, WikiTree):
                print ' '*i+'('+x.name
                for c in x:
                    f(c, i+1)
            elif isinstance(x, WikiToken):
                print ' '*i+x.name
            elif isinstance(x, XMLTagToken):
                print ' '*i+x.name
            elif isinstance(x, basestring):
                print ' '*i+repr(x)
            else:
                assert 0, x
        f(parser.get_root())
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
