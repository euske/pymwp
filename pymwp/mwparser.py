#!/usr/bin/env python
import sys
from mwtokenizer import WikiToken
from mwtokenizer import ExtensionToken
from mwtokenizer import WikiHeadlineToken
from mwtokenizer import WikiItemizeToken
from mwtokenizer import XMLTagToken
from mwtokenizer import XMLStartTagToken
from mwtokenizer import XMLEndTagToken
from mwtokenizer import WikiTextTokenizer


##  WikiParserError
##
class WikiParserError(ValueError): pass
class WikiParserStackOverflow(WikiParserError): pass


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
        s = ''
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

class WikiExtensionTree(WikiTree):
    def __init__(self, token):
        WikiTree.__init__(self)
        self.token = token
        return
    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.token)
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

    XML_PAR_END = frozenset(
        [ XMLStartTagToken(name) for name in XMLTagToken.PAR_TAG ]
        )
    XML_TABLE_ROW_END = frozenset(
        [ XMLStartTagToken(name) for name in XMLTagToken.TABLE_ROW_TAG ]
        )

    def __init__(self, maxdepth=100):
        WikiTextTokenizer.__init__(self)
        self.maxdepth = maxdepth
        self._tree = self._root = WikiPageTree()
        self._parse = self._parse_top
        self._stoptokens = set()
        self._stack = [(self._tree, self._parse, self._stoptokens)]
        return

    def get_root(self):
        return self._root

    def feed_token(self, pos, token):
        while 1:
            #print (token, self._parse, self._stoptokens)
            if self._parse(pos, token): break
        return

    def handle_token(self, pos, token):
        WikiTextTokenizer.handle_token(self, pos, token)
        self.feed_token(pos, token)
        return

    def handle_text(self, pos, text):
        WikiTextTokenizer.handle_text(self, pos, text)
        self.feed_token(pos, text)
        return

    def invalid_token(self, pos, token):
        print >>sys.stderr, (self._parse, pos, token)
        return

    def _push_context(self, tree, parse, stoptokens=None, newcontext=False):
        if self.maxdepth <= len(self._stack): raise WikiParserStackOverflow
        self._tree.append(tree)
        self._tree = tree
        self._parse = parse
        if newcontext:
            self._stoptokens = set()
        if stoptokens is not None:
            self._stoptokens = self._stoptokens.copy()
            self._stoptokens.update(stoptokens)
        self._stack.append((self._tree, self._parse, self._stoptokens))
        return

    def _pop_context(self):
        assert self._stack
        self._tree.finish()
        self._stack.pop()
        (self._tree, self._parse, self._stoptokens) = self._stack[-1]
        return

    def _is_closing(self, t):
        return ((isinstance(t, WikiToken) and t in self._stoptokens) or
                (isinstance(t, XMLTagToken) and t in self._stoptokens))

    # _parse_top: initial state.
    def _parse_top(self, pos, t):
        if isinstance(t, ExtensionToken):
            # Extention tag.
            self._push_context(WikiExtensionTree(t), self._parse_par)
            return True
        else:
            return self._parse_par(pos, t)

    # _parse_par: beginning of paragraph.
    def _parse_par(self, pos, t):
        if t in (
            WikiToken.HR,
            WikiToken.PAR):
            self._tree.append(t)
            return True
        elif isinstance(t, WikiItemizeToken):
            self._push_context(WikiItemizeTree(t), self._parse_itemize)
            return True
        elif isinstance(t, WikiHeadlineToken):
            self._push_context(WikiHeadlineTree(t), self._parse_headline)
            return True
        elif t is WikiToken.PRE:
            self._push_context(WikiPreTree(t), self._parse_pre)
            return True
        elif t is WikiToken.TABLE_OPEN:
            self._push_context(WikiTableTree(t), self._parse_table)
            return True
        else:
            return self._parse_base(pos, t)
            
    # _parse_itemize: *:#
    def _parse_itemize(self, pos, t):
        assert isinstance(self._tree, WikiItemizeTree), self._tree
        if t is WikiToken.EOL:
            # End of itemize.
            self._pop_context()
            return True
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            return self._parse_par(pos, t)
        
    # _parse_headline: === ... ===
    def _parse_headline(self, pos, t):
        assert isinstance(self._tree, WikiHeadlineTree), self._tree
        if t is self._tree.token:
            # End of headline.
            self._pop_context()
            return True
        elif t is WikiToken.EOL:
            # FAILSAFE: missing headline token.
            self._pop_context()
            return True
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            return self._parse_base(pos, t)
        
    # _parse_pre:
    def _parse_pre(self, pos, t):
        assert isinstance(self._tree, WikiPreTree), self._tree
        if t is WikiToken.EOL:
            # End of pre.
            self._pop_context()
            return True
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            return self._parse_base(pos, t)

    # _parse_table: {| ...
    def _parse_table(self, pos, t):
        assert isinstance(self._tree, WikiTableTree), self._tree
        if t is WikiToken.TABLE_CLOSE:
            # End of table.
            self._pop_context()
            return True
        elif t is WikiToken.TABLE_CAPTION:
            # Start of table caption.
            self._push_context(WikiTableCaptionTree(t), self._parse_table_caption)
            return True
        elif t is WikiToken.TABLE_ROW:
            # Start of table row.
            self._push_context(WikiTableRowTree(t), self._parse_table_row)
            return True
        elif t in (
                WikiToken.TABLE_HEADER,
                WikiToken.TABLE_HEADER_SEP,
                WikiToken.TABLE_DATA,
                WikiToken.TABLE_DATA_SEP):
            # FAILSAFE: missing table row token.
            self._push_context(WikiTableRowTree(t), self._parse_table_row)
            return False
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            # Anything else is table argument.
            self._push_context(WikiArgTree(), self._parse_table_arg)
            return False

    # _parse_table_caption: |+ ...
    def _parse_table_caption(self, pos, t):
        assert isinstance(self._tree, WikiTableCaptionTree), self._tree
        if t is WikiToken.EOL:
            # End of table caption.
            self._pop_context()
            return True
        elif t in (
                WikiToken.TABLE_CLOSE,
                WikiToken.TABLE_CAPTION,
                WikiToken.TABLE_ROW,
                WikiToken.TABLE_HEADER,
                WikiToken.TABLE_HEADER_SEP,
                WikiToken.TABLE_DATA,
                WikiToken.TABLE_DATA_SEP):
            # FAILSAFE: missing tokens.
            self._pop_context()
            return False
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            # Anything else is table argument.
            self._push_context(WikiArgTree(), self._parse_table_arg)
            return False
        
    # _parse_table_row: |- ...
    def _parse_table_row(self, pos, t):
        assert isinstance(self._tree, WikiTableRowTree), self._tree
        if t is WikiToken.EOL:
            # End of table row.
            self._pop_context()
            return True
        elif t in (
                WikiToken.TABLE_HEADER,
                WikiToken.TABLE_HEADER_SEP):
            # Start of table header.
            self._push_context(WikiTableHeaderTree(t), self._parse_table_header)
            return True
        elif t in (
                WikiToken.TABLE_DATA,
                WikiToken.TABLE_DATA_SEP):
            # Start of table data.
            self._push_context(WikiTableDataTree(t), self._parse_table_data)
            return True
        elif t in (
                WikiToken.TABLE_CLOSE,
                WikiToken.TABLE_CAPTION,
                WikiToken.TABLE_ROW):
            # FAILSAFE: missing tokens.
            self._pop_context()
            return False
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            # Anything else is table argument.
            self._push_context(WikiArgTree(), self._parse_table_arg)
            return False

    # _parse_table_header: ! ... !! ...
    def _parse_table_header(self, pos, t):
        assert isinstance(self._tree, WikiTableHeaderTree), self._tree
        if t is WikiToken.EOL:
            # End of table header.
            self._pop_context()
            return True
        elif t is WikiToken.TABLE_HEADER_SEP:
            # Next table header.
            self._pop_context()
            return False
        elif t in (
                WikiToken.TABLE_CLOSE,
                WikiToken.TABLE_CAPTION,
                WikiToken.TABLE_ROW,
                WikiToken.TABLE_HEADER,
                WikiToken.TABLE_DATA,
                WikiToken.TABLE_DATA_SEP):
            # FAILSAFE: missing tokens.
            self._pop_context()
            return False
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            # Anything else is table argument.
            self._push_context(WikiArgTree(), self._parse_table_arg)
            return False

    # _parse_table_data: | ... || ...
    def _parse_table_data(self, pos, t):
        assert isinstance(self._tree, WikiTableDataTree), self._tree
        if t is WikiToken.EOL:
            # End of table data.
            self._pop_context()
            return True
        elif t is WikiToken.TABLE_DATA_SEP:
            # Next table data.
            self._pop_context()
            return False
        elif t in (
                WikiToken.TABLE_CLOSE,
                WikiToken.TABLE_CAPTION,
                WikiToken.TABLE_ROW,
                WikiToken.TABLE_HEADER,
                WikiToken.TABLE_HEADER_SEP,
                WikiToken.TABLE_DATA):
            # FAILSAFE: missing tokens.
            self._pop_context()
            return False
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            # Anything else is table argument.
            self._push_context(WikiArgTree(), self._parse_table_arg)
            return False

    # _parse_table_arg:
    def _parse_table_arg(self, pos, t):
        assert isinstance(self._tree, WikiArgTree), self._tree
        if t is WikiToken.EOL:
            # End of table argument.
            self._pop_context()
            return True
        elif t is WikiToken.BAR:
            # Next table argument.
            self._pop_context()
            return True
        elif t in (
                WikiToken.TABLE_CLOSE,
                WikiToken.TABLE_CAPTION,
                WikiToken.TABLE_ROW,
                WikiToken.TABLE_HEADER,
                WikiToken.TABLE_HEADER_SEP,
                WikiToken.TABLE_DATA,
                WikiToken.TABLE_DATA_SEP):
            # FAILSAFE: missing tokens.
            self._pop_context()
            return False
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            return self._parse_base(pos, t)
            
    # _parse_base: generic parse state.
    def _parse_base(self, pos, t):
        if t is WikiToken.SPECIAL_OPEN:
            self._push_context(WikiSpecialTree(t), self._parse_special)
            return True
        elif t is WikiToken.KEYWORD_OPEN:
            self._push_context(WikiKeywordTree(t), self._parse_keyword)
            return True
        elif t is WikiToken.LINK_OPEN:
            self._push_context(WikiLinkTree(t), self._parse_link)
            return True
        elif t in (
            WikiToken.QUOTE2,
            WikiToken.QUOTE3,
            WikiToken.QUOTE5):
            self._push_context(WikiSpanTree(t), self._parse_span)
            return True
        elif t is WikiToken.COMMENT_OPEN:
            self._push_context(WikiCommentTree(t), self._parse_comment)
            return True
        elif isinstance(t, WikiToken):
            # any unhandled wiki token.
            self._tree.append(t)
            return True
        elif isinstance(t, XMLStartTagToken) and t.name in XMLTagToken.TABLE_TAG:
            self._push_context(WikiXMLTableTree(t), self._parse_xml_table,
                               newcontext=True)
            return True
        elif isinstance(t, XMLStartTagToken) and t.name in XMLTagToken.PAR_TAG:
            self._push_context(WikiXMLParTree(t), self._parse_xml_par,
                               stoptokens=self.XML_PAR_END)
            return True
        elif isinstance(t, XMLStartTagToken):
            self._push_context(WikiXMLTree(t), self._parse_xml)
            return True
        elif isinstance(t, XMLTagToken):
            # any unhandled XML token.
            self._tree.append(t)
            return True
        elif isinstance(t, basestring):
            # text string.
            self._tree.append(t)
            return True
        else:
            self.invalid_token(pos, t)
            return True


    # _parse_special: {{ ... }}
    def _parse_special(self, pos, t):
        assert isinstance(self._tree, WikiSpecialTree), self._tree
        if t is WikiToken.SPECIAL_CLOSE:
            # End of special.
            self._pop_context()
            return True
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            self._push_context(WikiArgTree(), self._parse_arg_barsep,
                               stoptokens=(WikiToken.SPECIAL_CLOSE,))
            return False

    # _parse_keyword: [[ ... ]]
    def _parse_keyword(self, pos, t):
        assert isinstance(self._tree, WikiKeywordTree), self._tree
        if t is WikiToken.KEYWORD_CLOSE:
            # End of keyword.
            self._pop_context()
            return True
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            self._push_context(WikiArgTree(), self._parse_arg_barsep,
                               stoptokens=(WikiToken.KEYWORD_CLOSE,))
            return False
        
    # _parse_link: [ ... ]
    def _parse_link(self, pos, t):
        assert isinstance(self._tree, WikiLinkTree), self._tree
        if t is WikiToken.LINK_CLOSE:
            # End of link.
            self._pop_context()
            return True
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            self._push_context(WikiArgTree(), self._parse_arg_blanksep,
                               stoptokens=(WikiToken.LINK_CLOSE,))
            return False
    
    # _parse_span: ''...'', '''...''', etc.
    def _parse_span(self, pos, t):
        assert isinstance(self._tree, WikiSpanTree), self._tree
        if t is self._tree.token:
            # End of span.
            self._pop_context()
            return True
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            return self._parse_base(pos, t)
    
    # _parse_arg_barsep: ...|...|...
    def _parse_arg_barsep(self, pos, t):
        assert isinstance(self._tree, WikiArgTree), self._tree
        if t is WikiToken.BAR:
            # Next argument.
            self._pop_context()
            return True
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            return self._parse_base(pos, t)
    
    # _parse_arg_blanksep: ... ... ...
    def _parse_arg_blanksep(self, pos, t):
        assert isinstance(self._tree, WikiArgTree), self._tree
        if t is WikiToken.BLANK:
            # Next argument.
            self._pop_context()
            return True
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            return self._parse_base(pos, t)
            
    # _parse_comment: <!-- ... -->
    def _parse_comment(self, pos, t):
        assert isinstance(self._tree, WikiCommentTree), self._tree
        if t is WikiToken.COMMENT_CLOSE:
            # End of comment.
            self._pop_context()
            return True
        else:
            self._tree.append(t)
            return True
        
    # _parse_xml_table: handle XML table tags.
    def _parse_xml_table(self, pos, t):
        assert isinstance(self._tree, WikiXMLTableTree), self._tree
        if isinstance(t, XMLEndTagToken):
            # End of XML table.
            self._pop_context()
            return True
        elif (isinstance(t, XMLStartTagToken) and
              t.name in XMLTagToken.TABLE_ROW_TAG):
            self._push_context(WikiXMLTableRowTree(t),
                               self._parse_xml_table_row,
                               stoptokens=self.XML_TABLE_ROW_END)
            # Start <table>.
            return True
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            return self._parse_base(pos, t)
        
    # _parse_xml_table_row: handle XML table row tags.
    def _parse_xml_table_row(self, pos, t):
        assert isinstance(self._tree, WikiXMLTableRowTree), self._tree
        if isinstance(t, XMLEndTagToken):
            # End of XML table row.
            self._pop_context()
            return True
        elif (isinstance(t, XMLStartTagToken) and
              t.name in XMLTagToken.TABLE_ROW_TAG):
            # Start <tr>.
            self._pop_context()
            return False
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            return self._parse_par(pos, t)

    # _parse_xml_par: handle XML paragraph tags.
    def _parse_xml_par(self, pos, t):
        assert isinstance(self._tree, WikiXMLParTree), self._tree
        if isinstance(t, XMLEndTagToken):
            # End of XML paragraph.
            self._pop_context()
            return True
        elif t in (
                WikiToken.TABLE_CLOSE,
                WikiToken.TABLE_CAPTION,
                WikiToken.TABLE_ROW,
                WikiToken.TABLE_HEADER,
                WikiToken.TABLE_HEADER_SEP,
                WikiToken.TABLE_DATA,
                WikiToken.TABLE_DATA_SEP):
            # FAILSAFE: automatically close XML tag before any table token.
            self._pop_context()
            return False
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            return self._parse_par(pos, t)

    # _parse_xml: handle XML tags.
    def _parse_xml(self, pos, t):
        assert isinstance(self._tree, WikiXMLTree), self._tree
        if isinstance(t, XMLEndTagToken):
            # End of XML.
            self._pop_context()
            return True
        elif t in (
                WikiToken.TABLE_CLOSE,
                WikiToken.TABLE_CAPTION,
                WikiToken.TABLE_ROW,
                WikiToken.TABLE_HEADER,
                WikiToken.TABLE_HEADER_SEP,
                WikiToken.TABLE_DATA,
                WikiToken.TABLE_DATA_SEP):
            # FAILSAFE: automatically close XML tag before any table token.
            self._pop_context()
            return False
        elif self._is_closing(t):
            self._pop_context()
            return False
        else:
            return self._parse_base(pos, t)


# main
def main(argv):
    args = argv[1:] or ['-']
    codec = 'utf-8'
    for path in args:
        sys.stderr.write(path+'\n')
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
                print (' '*i+'('+repr(x))
                for c in x:
                    f(c, i+1)
                print (' '*i+')')
            elif isinstance(x, WikiToken):
                print (' '*i+repr(x))
            elif isinstance(x, XMLTagToken):
                print (' '*i+repr(x))
            elif isinstance(x, basestring):
                print (' '*i+repr(x))
            else:
                assert 0, x
        f(parser.get_root())
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
