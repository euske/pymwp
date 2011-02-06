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

    def __init__(self):
        self._subtree = []
        return

    def __repr__(self):
        return ('<%s>' % self.__class__.__name__)

    def __iter__(self):
        return iter(self._subtree)

    def __len__(self):
        return len(self._subtree)

    def __getitem__(self, i):
        return self._subtree[i]

    def __getslice__(self, i, j):
        return self._subtree[i:j]

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

    def finish(self):
        return

class WikiPageTree(WikiTree): pass
class WikiArgTree(WikiTree): pass

class WikiSpanTree(WikiTree):
    def __init__(self, token):
        WikiTree.__init__(self)
        self.token = token
        return
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.token)
class WikiDivTree(WikiTree):
    def __init__(self, token):
        WikiTree.__init__(self)
        self.token = token
        return
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.token)
class WikiXMLTree(WikiTree):
    def __init__(self, xml):
        WikiTree.__init__(self)
        self.xml = xml
        return
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.xml)
    def get_attr(self, name, value=None):
        return self.xml.get_attr(name, value=value)
class WikiXMLParTree(WikiXMLTree): pass
class WikiXMLTableTree(WikiXMLTree): pass
class WikiXMLTableRowTree(WikiXMLTree): pass
class WikiCommentTree(WikiSpanTree): pass
class WikiSpecialTree(WikiSpanTree): pass
class WikiKeywordTree(WikiSpanTree): pass
class WikiLinkTree(WikiSpanTree): pass
class WikiTableTree(WikiDivTree): pass
class WikiTableCaptionTree(WikiTableTree): pass
class WikiTableRowTree(WikiTableTree): pass
class WikiTableCellTree(WikiTableTree): pass
class WikiTableHeaderTree(WikiTableCellTree): pass
class WikiTableDataTree(WikiTableCellTree): pass
class WikiPreTree(WikiDivTree): pass
class WikiItemizeTree(WikiDivTree): pass
class WikiHeadlineTree(WikiDivTree): pass


##  WikiTextParser
##
class WikiTextParser(WikiTextTokenizer):

    TABLE = (
        WikiToken.TABLE_CAPTION,
        WikiToken.TABLE_ROW,
        WikiToken.TABLE_HEADER,
        WikiToken.TABLE_HEADER_SEP,
        WikiToken.TABLE_DATA,
        WikiToken.TABLE_DATA_SEP,
        )

    def __init__(self):
        WikiTextTokenizer.__init__(self)
        self._root = WikiPageTree()
        self._stack = [(self._root, self._parse_top, set())]
        (self._tree, self._parse, self._stoptokens) = self._stack.pop()
        return

    def get_root(self):
        return self._root

    def feed_tokens(self, tokens):
        i = 0
        while 0 <= i and i < len(tokens):
            #print self._parse, tokens[i]
            i = self._parse(i, tokens[i])
            assert i is not None
        return

    def handle_token(self, pos, token):
        WikiTextTokenizer.handle_token(self, pos, token)
        self.feed_tokens([(pos, token)])
        return

    def handle_text(self, pos, text):
        WikiTextTokenizer.handle_text(self, pos, text)
        self.feed_tokens([(pos, text)])
        return

    def invalid_token(self, pos, token):
        print >>sys.stderr, (self._parse, pos, token)
        return

    def _push_context(self, tree, parse, stoptoken=None):
        self._tree.append(tree)
        self._stack.append((self._tree, self._parse, self._stoptokens))
        self._tree = tree
        self._parse = parse
        if stoptoken is not None:
            self._stoptokens = self._stoptokens.copy()
            self._stoptokens.add(stoptoken)
        return

    def _pop_context(self):
        assert self._stack
        self._tree.finish()
        (self._tree, self._parse, self._stoptokens) = self._stack.pop()
        return

    def _is_closing(self, t):
        return ((isinstance(t, WikiToken) and t in self._stoptokens) or
                (isinstance(t, XMLEndTagToken) and t.name in self._stoptokens))

    def _parse_top(self, i, (pos,t)):
        if isinstance(t, XMLStartTagToken) and t.name in XMLTagToken.TABLE_TAG:
            self._push_context(WikiXMLTableTree(t), self._parse_xml_table,
                               t.name)
            return i+1
        elif isinstance(t, XMLStartTagToken) and t.name in XMLTagToken.PAR_TAG:
            self._push_context(WikiXMLParTree(t), self._parse_xml_par,
                               t.name)
            return i+1
        elif isinstance(t, XMLStartTagToken):
            self._push_context(WikiXMLTree(t), self._parse_xml,
                               t.name)
            return i+1
        elif isinstance(t, WikiItemizeToken):
            self._push_context(WikiItemizeTree(t), self._parse_itemize)
            return i+1
        elif isinstance(t, WikiHeadlineToken):
            self._push_context(WikiHeadlineTree(t), self._parse_headline)
            return i+1
        elif t is WikiToken.PRE:
            self._push_context(WikiPreTree(t), self._parse_pre)
            return i+1
        elif t is WikiToken.TABLE_OPEN:
            self._push_context(WikiTableTree(t), self._parse_table,
                               WikiToken.TABLE_CLOSE)
            return i+1
        elif t is WikiToken.COMMENT_OPEN:
            self._push_context(WikiCommentTree(t), self._parse_comment,
                               WikiToken.COMMENT_CLOSE)
            return i+1
        elif t is WikiToken.SPECIAL_OPEN:
            self._push_context(WikiSpecialTree(t), self._parse_special,
                               WikiToken.SPECIAL_CLOSE)
            return i+1
        elif t is WikiToken.KEYWORD_OPEN:
            self._push_context(WikiKeywordTree(t), self._parse_keyword,
                               WikiToken.KEYWORD_CLOSE)
            return i+1
        elif t is WikiToken.LINK_OPEN:
            self._push_context(WikiLinkTree(t), self._parse_link,
                               WikiToken.LINK_CLOSE)                               
            return i+1
        elif t in (
            WikiToken.QUOTE2,
            WikiToken.QUOTE3,
            WikiToken.QUOTE5):
            self._push_context(WikiSpanTree(t), self._parse_span, t)
            return i+1
        elif t in (
            WikiToken.HR,
            WikiToken.PAR,
            WikiToken.PRE):
            self._tree.append(t)
            return i+1
        elif isinstance(t, XMLTagToken):
            self._tree.append(t)
            return i+1
        elif isinstance(t, WikiToken):
            self._tree.append(unicode(t.name))
            return i+1
        elif isinstance(t, basestring):
            self._tree.append(t)
            return i+1
        else:
            self.invalid_token(pos, t)
            return i+1

    def _parse_comment(self, i, (pos,t)):
        assert isinstance(self._tree, WikiCommentTree), self._tree
        if t is WikiToken.COMMENT_CLOSE:
            self._pop_context()
            return i+1
        else:
            self._tree.append(t)
            return i+1
        
    def _parse_xml(self, i, (pos,t)):
        assert isinstance(self._tree, WikiXMLTree), self._tree
        if isinstance(t, XMLEndTagToken):
            self._pop_context()
            return i+1
        elif t in self.TABLE:
            # automatically close xml tag before tables.
            self._pop_context()
            return i
        elif self._is_closing(t):
            self._pop_context()
            return i
        else:
            return self._parse_top(i, (pos,t))

    def _parse_xml_par(self, i, (pos,t)):
        assert isinstance(self._tree, WikiXMLParTree), self._tree
        if isinstance(t, XMLEndTagToken):
            self._pop_context()
            return i+1
        elif isinstance(t, XMLStartTagToken) and t.name in XMLTagToken.PAR_TAG:
            self._pop_context()
            return i
        elif isinstance(t, XMLStartTagToken) and t.name in XMLTagToken.TABLE_ROW_TAG:
            self._pop_context()
            return i
        elif t in self.TABLE:
            # automatically close xml tag before tables.
            self._pop_context()
            return i
        elif self._is_closing(t):
            self._pop_context()
            return i
        else:
            return self._parse_top(i, (pos,t))

    def _parse_xml_table(self, i, (pos,t)):
        assert isinstance(self._tree, WikiXMLTableTree), self._tree
        if isinstance(t, XMLStartTagToken) and t.name in XMLTagToken.TABLE_ROW_TAG:
            self._push_context(WikiXMLTableRowTree(t), self._parse_xml_table_row,
                               t.name)
            return i+1
        elif isinstance(t, XMLEndTagToken):
            self._pop_context()
            return i+1
        elif self._is_closing(t):
            self._pop_context()
            return i
        else:
            return self._parse_top(i, (pos,t))
        
    def _parse_xml_table_row(self, i, (pos,t)):
        assert isinstance(self._tree, WikiXMLTableRowTree), self._tree
        if isinstance(t, XMLEndTagToken):
            self._pop_context()
            return i+1
        elif isinstance(t, XMLStartTagToken) and t.name in XMLTagToken.TABLE_ROW_TAG:
            self._pop_context()
            return i
        elif self._is_closing(t):
            self._pop_context()
            return i
        else:
            return self._parse_top(i, (pos,t))
        
    def _parse_special(self, i, (pos,t)):
        assert isinstance(self._tree, WikiSpecialTree), self._tree
        if t is WikiToken.SPECIAL_CLOSE:
            self._pop_context()
            return i+1
        elif self._is_closing(t):
            self._pop_context()
            return i
        else:
            self._push_context(WikiArgTree(), self._parse_arg_barsep,
                               WikiToken.BAR)
            return i

    def _parse_keyword(self, i, (pos,t)):
        assert isinstance(self._tree, WikiKeywordTree), self._tree
        if t is WikiToken.KEYWORD_CLOSE:
            self._pop_context()
            return i+1
        elif self._is_closing(t):
            self._pop_context()
            return i
        else:
            self._push_context(WikiArgTree(), self._parse_arg_barsep,
                               WikiToken.BAR)
            return i
        
    def _parse_link(self, i, (pos,t)):
        assert isinstance(self._tree, WikiLinkTree), self._tree
        if t is WikiToken.LINK_CLOSE:
            self._pop_context()
            return i+1
        elif self._is_closing(t):
            self._pop_context()
            return i
        else:
            self._push_context(WikiArgTree(), self._parse_arg_spcsep,
                               WikiToken.BLANK)
            return i
    
    def _parse_arg_barsep(self, i, (pos,t)):
        assert isinstance(self._tree, WikiArgTree), self._tree
        if t is WikiToken.BAR:
            self._pop_context()
            return i+1
        elif self._is_closing(t):
            self._pop_context()
            return i
        else:
            return self._parse_top(i, (pos,t))
    
    def _parse_arg_spcsep(self, i, (pos,t)):
        assert isinstance(self._tree, WikiArgTree), self._tree
        if t is WikiToken.BLANK:
            self._pop_context()
            return i+1
        elif self._is_closing(t):
            self._pop_context()
            return i
        else:
            return self._parse_top(i, (pos,t))
    
    def _parse_span(self, i, (pos,t)):
        assert isinstance(self._tree, WikiSpanTree), self._tree
        if t is self._tree.token:
            self._pop_context()
            return i+1
        elif self._is_closing(t):
            self._pop_context()
            return i
        else:
            return self._parse_top(i, (pos,t))
        
    def _parse_pre(self, i, (pos,t)):
        assert isinstance(self._tree, WikiPreTree), self._tree
        if t is WikiToken.EOL:
            self._pop_context()
            return i+1
        elif self._is_closing(t):
            self._pop_context()
            return i
        else:
            return self._parse_top(i, (pos,t))
        
    def _parse_itemize(self, i, (pos,t)):
        assert isinstance(self._tree, WikiItemizeTree), self._tree
        if t is WikiToken.EOL:
            self._pop_context()
            return i+1
        elif self._is_closing(t):
            self._pop_context()
            return i
        else:
            return self._parse_top(i, (pos,t))
        
    def _parse_headline(self, i, (pos,t)):
        assert isinstance(self._tree, WikiHeadlineTree), self._tree
        if t is WikiToken.EOL:
            self._pop_context()
            return i+1
        elif isinstance(t, WikiHeadlineToken):
            return i+1
        elif self._is_closing(t):
            self._pop_context()
            return i
        else:
            return self._parse_top(i, (pos,t))
        
    def _parse_table(self, i, (pos,t)):
        assert isinstance(self._tree, WikiTableTree), self._tree
        if t is WikiToken.TABLE_CLOSE:
            self._pop_context()
            return i+1
        elif t is WikiToken.TABLE_CAPTION:
            self._push_context(WikiTableCaptionTree(t), self._parse_table_caption)
            return i+1
        elif t is WikiToken.TABLE_ROW:
            self._push_context(WikiTableRowTree(t), self._parse_table_row)
            return i+1
        elif t in self.TABLE:
            self._push_context(WikiTableRowTree(t), self._parse_table_row)
            return i
        elif self._is_closing(t):
            self._pop_context()
            return i
        else:
            self._push_context(WikiArgTree(), self._parse_table_arg,
                               WikiToken.BAR)                               
            return i

    def _parse_table_arg(self, i, (pos,t)):
        assert isinstance(self._tree, WikiArgTree), self._tree
        if t is WikiToken.BAR:
            self._pop_context()
            return i+1
        elif t in self.TABLE:
            self._pop_context()            
            return i
        elif self._is_closing(t):
            self._pop_context()
            return i
        else:
            return self._parse_top(i, (pos,t))
        
    def _parse_table_caption(self, i, (pos,t)):
        assert isinstance(self._tree, WikiTableCaptionTree), self._tree
        if t is WikiToken.EOL:
            self._pop_context()
            return i+1
        elif t in self.TABLE:
            self._pop_context()            
            return i
        elif self._is_closing(t):
            self._pop_context()
            return i
        else:
            self._push_context(WikiArgTree(), self._parse_table_arg)
            return i
        
    def _parse_table_row(self, i, (pos,t)):
        assert isinstance(self._tree, WikiTableRowTree), self._tree
        if t is WikiToken.EOL:
            self._pop_context()
            return i+1
        elif t in (
            WikiToken.TABLE_HEADER,
            WikiToken.TABLE_HEADER_SEP):
            self._push_context(WikiTableHeaderTree(t), self._parse_table_header)
            return i+1
        elif t in (
            WikiToken.TABLE_DATA,
            WikiToken.TABLE_DATA_SEP):
            self._push_context(WikiTableDataTree(t), self._parse_table_data)
            return i+1
        elif t in self.TABLE:
            self._pop_context()
            return i
        elif self._is_closing(t):
            self._pop_context()
            return i
        else:
            self._push_context(WikiArgTree(), self._parse_table_arg)
            return i
        
    def _parse_table_header(self, i, (pos,t)):
        assert isinstance(self._tree, WikiTableHeaderTree), self._tree
        if t is WikiToken.EOL:
            self._pop_context()
            return i+1
        elif t in self.TABLE:
            self._pop_context()            
            return i
        elif self._is_closing(t):
            self._pop_context()            
            return i
        else:
            self._push_context(WikiArgTree(), self._parse_table_arg)
            return i

    def _parse_table_data(self, i, (pos,t)):
        assert isinstance(self._tree, WikiTableDataTree), self._tree
        if t is WikiToken.EOL:
            self._pop_context()
            return i+1
        elif t in self.TABLE:
            self._pop_context()            
            return i
        elif self._is_closing(t):
            self._pop_context()            
            return i
        else:
            self._push_context(WikiArgTree(), self._parse_table_arg)
            return i


# main
def main(argv):
    args = argv[1:] or ['-']
    codec = 'utf-8'
    for path in args:
        print >>sys.stderr, path
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
                print ' '*i+'('+repr(x)
                for c in x:
                    f(c, i+1)
                print ' '*i+')'
            elif isinstance(x, WikiToken):
                print ' '*i+repr(x)
            elif isinstance(x, XMLTagToken):
                print ' '*i+repr(x)
            elif isinstance(x, basestring):
                print ' '*i+repr(x)
            else:
                assert 0, x
        f(parser.get_root())
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
