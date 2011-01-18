#!/usr/bin/env python2
# usage:
#   $ bzip2 -dc jawiki-dumps.xml.bz2 | python2 wp.py
#
import sys
from htmlentitydefs import name2codepoint
from xml.parsers.expat import ParserCreate


##  Token
##
class Token(object):
    
    def __init__(self):
        return
    
    def add_char(self, c):
        return


##  WikiToken
##
class WikiToken(Token):

    def __init__(self, name=u''):
        self.name = name
        return
    
    def __repr__(self):
        return '<wiki %s>' % self.name
    
    def add_char(self, c):
        self.name += c
        return

class WikiHeadlineToken(WikiToken): pass

class WikiBulletToken(WikiToken): pass

WikiToken.EOL = WikiToken('EOL')
WikiToken.BLANK = WikiToken('BLANK')
WikiToken.PAR = WikiToken('PAR')
WikiToken.PRE = WikiToken('PRE')
WikiToken.HR = WikiToken('HR')
WikiToken.QUOTE2 = WikiToken('QUOTE2')
WikiToken.QUOTE3 = WikiToken('QUOTE3')
WikiToken.QUOTE5 = WikiToken('QUOTE5')
WikiToken.BAR = WikiToken('|')
WikiToken.COMMENT_OPEN = WikiToken('<!--')
WikiToken.COMMENT_CLOSE = WikiToken('-->')
WikiToken.KWD_OPEN = WikiToken('[[')
WikiToken.KWD_CLOSE = WikiToken(']]')
WikiToken.URL_OPEN = WikiToken('[')
WikiToken.URL_CLOSE = WikiToken(']')
WikiToken.SPECIAL_OPEN = WikiToken('{{')
WikiToken.SPECIAL_CLOSE = WikiToken('}}')
WikiToken.TABLE_OPEN = WikiToken('{|')
WikiToken.TABLE_CLOSE = WikiToken('|}')
WikiToken.TABLE_ROW = WikiToken('|-')
WikiToken.TABLE_CAPTION = WikiToken('|+')
WikiToken.TABLE_HEADER = WikiToken('!')
WikiToken.TABLE_HEADER_SEP = WikiToken('!!')
WikiToken.TABLE_DATA = WikiToken('|')
WikiToken.TABLE_DATA_SEP = WikiToken('||')
    

##  XMLTagToken
##
class XMLTagToken(Token):

    def __init__(self):
        self.name = u''
        return
    
    def __repr__(self):
        return '<xmltag %r>' % (self.name)
    
    def add_char(self, c):
        self.name += c.lower()
        return

class XMLEndTagToken(XMLTagToken): pass

class XMLStartTagToken(XMLTagToken):
    
    def __init__(self):
        XMLTagToken.__init__(self)
        self.attrs = []
        self._key = self._value = None
        return
    
    def __repr__(self):
        return '<xmltag %r%s>' % (self.name, ''.join( ' %r=%r' % (k,v) for (k,v) in self.attrs ))
    
    def add_char(self, c):
        if self._value is not None:
            self._value += c
        elif self._key is not None:
            self._key += c.lower()
        else:
            XMLTagToken.add_char(self, c)
        return

    def start_key(self):
        assert self._key is None, self._key
        self._key = u''
        return

    def start_value(self):
        assert self._key is not None
        assert self._value is None
        self._value = u''
        return

    def end_attr(self):
        assert self._key is not None
        if self._value is None:
            self.attrs.append((self._key, self._key))
        else:
            self.attrs.append((self._key, self._value))
        self._key = self._value = None
        return


##  WikiTextTokenizer
##
class WikiTextTokenizer(object):

    class XMLEntityContext(object):
        def __init__(self, handler, state):
            self.handler = handler
            self.state = state
            self.name = u''
            return

    def __init__(self):
        self._scan = self._scan_bol
        self._wiki = True
        self._token = None
        self._entity = None
        self._line_token = None
        self._quote_close = None
        return

    def feed_text(self, text):
        i = 0
        while 0 <= i and i < len(text):
            assert isinstance(i, int)
            i = self._scan(i, text[i])
        return

    def finish(self):
        return

    def handle_token(self, token):
        if isinstance(token, XMLTagToken) and token.name == 'nowiki':
            self._wiki = False
        elif isinstance(token, XMLTagToken) and token.name == '/nowiki':
            self._wiki = True
        return

    def handle_char(self, c):
        return

    def _scan_bol(self, i, c):
        if c == '\n':
            self.handle_token(WikiToken.PAR)
            self._scan = self._scan_bol_nl
            return i+1
        elif c == '-':
            self._scan = self._scan_bol_hr
            return i+1
        elif c == '{':
            self._scan = self._scan_bol_brace
            return i+1
        elif c == '|':
            self._scan = self._scan_bol_bar
            return i+1
        elif c == '!':
            self.handle_token(WikiToken.TABLE_HEADER)
            self._scan = self._scan_main
            return i+1
        elif c == '=':
            self._token = WikiHeadlineToken()
            self._line_token = self._token
            self._scan = self._scan_bol_headline
            return i
        elif c in '*#:;':
            self._token = WikiBulletToken()
            self._line_token = self._token
            self._scan = self._scan_bol_bullet
            return i
        elif c.isspace():
            self._scan = self._scan_bol_sp
            return i+1
        else:
            self._scan = self._scan_main
            return i

    def _scan_bol_nl(self, i, c):
        if c == '\n':
            return i+1
        else:
            self._scan = self._scan_bol
            return i

    def _scan_bol_sp(self, i, c):
        if c == '\n':
            self._scan = self._scan_bol
            return i+1
        elif c.isspace():
            return i+1
        else:
            self.handle_token(WikiToken.PRE)
            self._scan = self._scan_main
            return i

    def _scan_bol_hr(self, i, c):
        if c == '-':
            return i+1
        else:
            self.handle_token(WikiToken.HR)
            self._scan = self._scan_main
            return i
        
    def _scan_bol_brace(self, i, c):
        if c == '|':
            self.handle_token(WikiToken.TABLE_OPEN)
            self._scan = self._scan_main
            return i+1
        else:
            self._scan = self._scan_brace_open
            return i
        
    def _scan_bol_bar(self, i, c):
        if c == '}':
            self.handle_token(WikiToken.TABLE_CLOSE)
            self._scan = self._scan_main
            return i+1
        elif c == '+':
            self.handle_token(WikiToken.TABLE_CAPTION)
            self._scan = self._scan_main
            return i+1            
        elif c == '-':
            self.handle_token(WikiToken.TABLE_ROW)
            self._scan = self._scan_main
            return i+1            
        else:
            self.handle_token(WikiToken.TABLE_DATA)
            self._line_token = WikiToken.TABLE_DATA
            self._scan = self._scan_main
            return i
    
    def _scan_bol_headline(self, i, c):
        assert isinstance(self._token, WikiHeadlineToken), self._token
        if c == '=':
            self._token.add_char(c)
            return i+1
        else:
            self.handle_token(self._token)
            self._token = None
            self._scan = self._scan_main
            return i

    def _scan_bol_bullet(self, i, c):
        assert isinstance(self._token, WikiBulletToken), self._token
        if c in '*#:;':
            self._token.add_char(c)
            return i+1
        else:
            self.handle_token(self._token)
            self._token = None
            self._scan = self._scan_main
            return i

    def _scan_main(self, i, c):
        assert self._token is None, self._token
        if c == '&':
            self._entity = self.XMLEntityContext(self.handle_char, self._scan_main)
            self._scan = self._scan_entity
            return i+1
        elif c == '<':
            self._scan = self._scan_tag
            return i+1
        elif not self._wiki:
            self.handle_char(c)
        elif c == '\n':
            self.handle_token(WikiToken.EOL)
            self._line_token = None
            self._scan = self._scan_bol
            return i+1
        elif c.isspace():
            self.handle_token(WikiToken.BLANK)
            self._scan = self._scan_blank
            return i+1
        elif c == '[':
            self._scan = self._scan_bracket_open
            return i+1
        elif c == ']':
            self._scan = self._scan_bracket_close
            return i+1
        elif c == '{':
            self._scan = self._scan_brace_open
            return i+1
        elif c == '}':
            self._scan = self._scan_brace_close
            return i+1
        elif c == "'":
            self._scan = self._scan_q1
            return i+1
        elif c == '|' and self._line_token is WikiToken.TABLE_DATA:
            self._scan = self._scan_bar
            return i+1
        elif c == '|':
            self.handle_token(WikiToken.BAR)
            return i+1
        elif c == '!' and self._line_token is WikiToken.TABLE_DATA:
            self._scan = self._scan_exc
            return i+1
        elif c == '=' and isinstance(self._line_token, WikiHeadlineToken):
            self.handle_token(self._line_token)
            self._scan = self._scan_headline_end
            return i
        else:
            self.handle_char(c)
            return i+1

    def _scan_headline_end(self, i, c):
        if c == '=':
            return i+1
        else:
            self._scan = self._scan_main
            return i
        
    def _scan_blank(self, i, c):
        if c.isspace():
            return i+1
        else:
            self._scan = self._scan_main
            return i
        
    def _scan_entity(self, i, c):
        assert self._entity is not None
        if c == '#':
            self._scan = self._scan_ent_numhex
            return i+1
        else:
            self._scan = self._scan_ent_name
            return i

    def _scan_ent_numhex(self, i, c):
        assert self._entity is not None
        if c == 'x' or c == 'X':
            self._scan = self._scan_ent_hex
            return i+1
        else:
            self._scan = self._scan_ent_num
            return i

    def _scan_ent_hex(self, i, c):
        assert self._entity is not None
        if c.isalnum():
            self._entity.name += c
            return i+1
        else:
            try:
                n = int(self._entity.name, 16)
                self._entity.handler(unichr(n))
            except ValueError:
                pass
            self._scan = self._entity.state
            self._entity = None
            if c == ';':
                return i+1
            else:
                return i

    def _scan_ent_num(self, i, c):
        assert self._entity is not None
        if c.isdigit():
            self._entity.name += c
            return i+1
        else:
            try:
                n = int(self._entity.name)
                self._entity.handler(unichr(n))
            except ValueError:
                pass
            self._scan = self._entity.state
            self._entity = None
            if c == ';':
                return i+1
            else:
                return i

    def _scan_ent_name(self, i, c):
        assert self._entity is not None
        if c.isalnum():
            self._entity.name += c
            return i+1
        else:
            try:
                n = name2codepoint[self._entity.name]
                self._entity.handler(unichr(n))
            except KeyError:
                pass
            self._scan = self._entity.state
            self._entity = None
            if c == ';':
                return i+1
            else:
                return i

    def _scan_tag(self, i, c):
        if c == '!':
            self.handle_token(WikiToken.COMMENT_OPEN)
            self._scan = self._scan_comment
            return i+1
        elif c == '/':
            self._token = XMLEndTagToken()
            self._scan = self._scan_endtag
            return i
        else:
            self._token = XMLStartTagToken()
            self._scan = self._scan_starttag_name
            return i
    
    def _scan_starttag_name(self, i, c):
        assert isinstance(self._token, XMLStartTagToken), self._token
        if c == '/':
            self._token.add_char(c)
            self._scan = self._scan_starttag_end
            return i+1
        elif c.isalnum():
            self._token.add_char(c)
            return i+1
        else:
            self._scan = self._scan_starttag_mid
            return i

    def _scan_starttag_end(self, i, c):
        assert isinstance(self._token, XMLStartTagToken), self._token
        if c == '>':
            self.handle_token(self._token)
            self._token = None
            self._scan = self._scan_main
            return i+1
        else:
            return i+1

    def _scan_starttag_mid(self, i, c):
        assert isinstance(self._token, XMLStartTagToken), self._token
        if c == '>':
            self.handle_token(self._token)
            self._token = None
            self._scan = self._scan_main
            return i+1
        elif c == '/':
            self._scan = self._scan_starttag_end
            return i+1
        elif c.isspace():
            return i+1
        else:
            self._token.start_key()
            self._scan = self._scan_starttag_attr_key
            return i
    
    def _scan_starttag_attr_key(self, i, c):
        assert isinstance(self._token, XMLStartTagToken), self._token
        if c == '=':
            self._token.start_value()
            self._scan = self._scan_starttag_attr_value
            return i+1
        elif c == '>' or c.isspace():
            self._token.end_attr()
            self._scan = self._scan_starttag_mid
            return i
        else:
            self._token.add_char(c)
            return i+1
    
    def _scan_starttag_attr_value(self, i, c):
        assert isinstance(self._token, XMLStartTagToken), self._token
        if c == '"':
            self._scan = self._scan_starttag_attr_value_quote
            self._quote_close = c
            return i+1
        elif c == "'":
            self._scan = self._scan_starttag_attr_value_quote
            self._quote_close = c
            return i+1
        elif c == '&':
            self._entity = self.XMLEntityContext(self._add_value_char,
                                                 self._scan_starttag_attr_value)
            self._scan = self._scan_entity
            return i+1
        elif c == '>' or c.isspace():
            self._token.end_attr()
            self._scan = self._scan_starttag_mid
            return i
        else:
            self._token.add_char(c)
            return i+1

    def _scan_starttag_attr_value_quote(self, i, c):
        assert isinstance(self._token, XMLStartTagToken), self._token
        assert self._quote_close is not None
        if c == self._quote_close:
            self._token.end_attr()
            self._quote_close = None
            self._scan = self._scan_starttag_mid
            return i+1
        elif c == '&':
            self._entity = self.XMLEntityContext(self._add_value_char,
                                                 self._scan_starttag_attr_value_quote)
            self._scan = self._scan_entity
            return i+1
        else:
            self._token.add_char(c)
            return i+1

    def _add_value_char(self, c):
        assert isinstance(self._token, XMLStartTagToken), self._token
        self._token.add_char(c)
        return

    def _scan_endtag(self, i, c):
        assert isinstance(self._token, XMLEndTagToken), self._token
        if c == '>':
            self.handle_token(self._token)
            self._token = None
            self._scan = self._scan_main
            return i+1
        elif c.isspace():
            return i+1
        else:
            self._token.add_char(c)
            return i+1

    def _scan_comment(self, i, c):
        # XXX not handling --
        if c == '>':
            self.handle_token(WikiToken.COMMENT_CLOSE)
            self._scan = self._scan_main
            return i+1
        else:
            self.handle_char(c)
            return i+1

    def _scan_bracket_open(self, i, c):
        if c == '[':
            self.handle_token(WikiToken.KWD_OPEN)
            self._scan = self._scan_main
            return i+1
        else:
            self.handle_token(WikiToken.URL_OPEN)
            self._scan = self._scan_main
            return i

    def _scan_bracket_close(self, i, c):
        if c == ']':
            self.handle_token(WikiToken.KWD_CLOSE)
            self._scan = self._scan_main
            return i+1
        else:
            self.handle_token(WikiToken.URL_CLOSE)
            self._scan = self._scan_main
            return i

    def _scan_brace_open(self, i, c):
        if c == '{':
            self.handle_token(WikiToken.SPECIAL_OPEN)
            self._scan = self._scan_main
            return i+1
        else:
            self.handle_char(u'{')
            self._scan = self._scan_main
            return i

    def _scan_brace_close(self, i, c):
        if c == '}':
            self.handle_token(WikiToken.SPECIAL_CLOSE)
            self._scan = self._scan_main
            return i+1
        else:
            self.handle_char(u'}')
            self._scan = self._scan_main
            return i

    def _scan_q1(self, i, c):
        if c == "'":
            self._scan = self._scan_q2
            return i+1
        else:
            self.handle_char(u"'")
            self._scan = self._scan_main
            return i
    
    def _scan_q2(self, i, c):
        if c == "'":
            self._scan = self._scan_q3
            return i+1
        else:
            self.handle_token(WikiToken.QUOTE2)
            self._scan = self._scan_main
            return i
    
    def _scan_q3(self, i, c):
        if c == "'":
            self._scan = self._scan_q4
            return i+1
        else:
            self.handle_token(WikiToken.QUOTE3)
            self._scan = self._scan_main
            return i

    def _scan_q4(self, i, c):
        if c == "'":
            self.handle_token(WikiToken.QUOTE5)
            self._scan = self._scan_main
            return i+1
        else:
            self._scan = self._scan_main
            return i

    def _scan_bar(self, i, c):
        if c == '|':
            self.handle_token(WikiToken.TABLE_DATA_SEP)
            self._scan = self._scan_main
            return i+1
        else:
            self.handle_char(u'|')
            self._scan = self._scan_main
            return i

    def _scan_exc(self, i, c):
        if c == '!':
            self.handle_token(WikiToken.TABLE_HEADER_SEP)
            self._scan = self._scan_main
            return i+1
        else:
            self.handle_char(u'!')
            self._scan = self._scan_main
            return i


##  WikiTree
##
class WikiTree(object):

    def __init__(self, name):
        self.name = name
        self.tokens = []
        return

    def __repr__(self):
        return '<%s %s>' % (self.name, ' '.join(map(repr, self.tokens)))

    def __iter__(self):
        return iter(self.tokens)

    def get_text(self):
        return iter(self)

    def append(self, token):
        self.tokens.append(token)
        return
    
    def finish(self):
        return

class WikiXMLTree(WikiTree):
    
    def __init__(self, xmltag):
        WikiTree.__init__(self, xmltag.name)
        self.xmltag = xmltag
        return

class WikiCommentTree(WikiTree):
    
    def __init__(self):
        WikiTree.__init__(self, 'comment')
        return
    
class WikiQuoteTree(WikiTree):
    
    def __init__(self, token):
        WikiTree.__init__(self, token.name)
        self.token = token
        return

class WikiPreTree(WikiTree):
    
    def __init__(self):
        WikiTree.__init__(self, 'pre')
        return

class WikiBulletTree(WikiTree):
    
    def __init__(self, token):
        WikiTree.__init__(self, token.name)
        return

class WikiHeadlineTree(WikiTree): 

    def __init__(self, token):
        WikiTree.__init__(self, 'headline'+str(len(token.name)))
        return

class WikiTableTree(WikiTree):
    
    def __init__(self):
        WikiTree.__init__(self, 'table')
        return

class WikiArgTree(WikiTree):
    
    def __init__(self, name):
        WikiTree.__init__(self, name)
        self.args = []
        self._arg1 = []
        return

    def __repr__(self):
        return '<%s %s>' % (self.name, ' '.join(map(repr, self.args)))

    def append(self, token):
        WikiTree.append(self, token)
        self._arg1.append(token)
        return
    
    def finish(self):
        self.args.append(self._arg1)
        WikiTree.finish(self)
        return

    def next_arg(self):
        self.args.append(self._arg1)
        self._arg1 = []
        return
    
class WikiKeywordTree(WikiArgTree):
    
    def __init__(self):
        WikiArgTree.__init__(self, 'keyword')
        return

    def get_text(self):
        if 2 <= len(self.args):
            return self.args[1]
        else:
            return self.args[0]

class WikiUrlTree(WikiArgTree):
    
    def __init__(self):
        WikiArgTree.__init__(self, 'url')
        return

    def get_text(self):
        if 2 <= len(self.args):
            return self.args[1]
        else:
            return self.args[0]

class WikiSpecialTree(WikiArgTree):
    
    def __init__(self):
        WikiArgTree.__init__(self, 'special')
        return


##  WikiTextParser
##
class WikiTextParser(WikiTextTokenizer):

    def __init__(self):
        WikiTextTokenizer.__init__(self)
        self._parse = self._parse_main
        self._stack = []
        self._root = self._tree = WikiTree('root')
        self._text = u''
        return

    def handle_token(self, token):
        WikiTextTokenizer.handle_token(self, token)
        if self._text:
            self._tree.append(self._text)
            self._text = u''
        self.feed_tokens([token])
        return

    def handle_char(self, c):
        WikiTextTokenizer.handle_char(self, c)
        self._text += c
        return

    def finish(self):
        if self._text:
            self._tree.append(self._text)
        WikiTextTokenizer.finish(self)
        return

    def get_root(self):
        return self._root

    def feed_tokens(self, tokens):
        i = 0
        while 0 <= i and i < len(tokens):
            assert isinstance(i, int)
            i = self._parse(i, tokens[i])
        return

    def _push_context(self, tree):
        self._tree.append(tree)
        self._stack.append((self._parse, self._tree))
        self._tree = tree
        return

    def _pop_context(self):
        assert self._stack
        self._tree.finish()
        (self._parse, self._tree) = self._stack.pop()
        return

    def _parse_main(self, i, t):
        if isinstance(t, XMLStartTagToken) and t.name.endswith('/'):
            self._tree.append(t)
            return i+1
        
        elif isinstance(t, XMLStartTagToken):
            self._push_context(WikiXMLTree(t))
            self._parse = self._parse_xml
            return i+1
        
        elif t is WikiToken.COMMENT_OPEN:
            self._push_context(WikiCommentTree())
            self._parse = self._parse_comment
            return i+1
            
        elif t is WikiToken.KWD_OPEN:
            self._push_context(WikiKeywordTree())
            self._parse = self._parse_keyword
            return i+1
        
        elif t is WikiToken.URL_OPEN:
            self._push_context(WikiUrlTree())
            self._parse = self._parse_url
            return i+1
        
        elif t is WikiToken.SPECIAL_OPEN:
            self._push_context(WikiSpecialTree())
            self._parse = self._parse_special
            return i+1
        
        elif t in (WikiToken.QUOTE2, WikiToken.QUOTE3, WikiToken.QUOTE5):
            self._push_context(WikiQuoteTree(t))
            self._parse = self._parse_quote
            return i+1
        
        elif t is WikiToken.PRE:
            self._push_context(WikiPreTree())
            self._parse = self._parse_pre
            return i+1

        elif t is WikiToken.TABLE_OPEN:
            self._push_context(WikiTableTree())
            self._parse = self._parse_table
            return i+1

        elif isinstance(t, WikiBulletToken):
            self._push_context(WikiBulletTree(t))
            self._parse = self._parse_bullet
            return i+1
        
        elif isinstance(t, WikiHeadlineToken):
            self._push_context(WikiHeadlineTree(t))
            self._parse = self._parse_headline
            return i+1

        elif t is WikiToken.HR:
            self._tree.append(t)
            return i+1
        elif t is WikiToken.PAR:
            self._tree.append(t)
            return i+1
        
        elif t is WikiToken.EOL:
            self._tree.append(u' ')
            return i+1
        elif t is WikiToken.BLANK:
            self._tree.append(u' ')
            return i+1
        elif t is WikiToken.BAR:
            self._tree.append(u'|')
            return i+1
        else:
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
        if t is WikiToken.BAR:
            self._tree.next_arg()
            return i+1
        elif t is WikiToken.KWD_CLOSE:
            self._pop_context()
            return i+1
        else:
            return self._parse_main(i, t)
    
    def _parse_url(self, i, t):
        assert isinstance(self._tree, WikiUrlTree), self._tree
        if t is WikiToken.BLANK:
            self._tree.next_arg()
            return i+1
        elif t is WikiToken.URL_CLOSE:
            self._pop_context()
            return i+1
        else:
            return self._parse_main(i, t)
    
    def _parse_special(self, i, t):
        assert isinstance(self._tree, WikiSpecialTree), self._tree
        if t is WikiToken.BAR:
            self._tree.next_arg()
            return i+1
        elif t is WikiToken.SPECIAL_CLOSE:
            self._pop_context()
            return i+1
        else:
            return self._parse_main(i, t)

    def _parse_quote(self, i, t):
        assert isinstance(self._tree, WikiQuoteTree), self._tree
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
        elif t is WikiToken.TABLE_ROW:
            return i+1
        elif t is WikiToken.TABLE_CAPTION:
            return i+1
        elif t is WikiToken.TABLE_HEADER:
            return i+1
        elif t is WikiToken.TABLE_HEADER_SEP:
            return i+1
        elif t is WikiToken.TABLE_DATA:
            return i+1
        elif t is WikiToken.TABLE_DATA_SEP:
            return i+1
        else:
            return self._parse_main(i, t)
        
    def _parse_bullet(self, i, t):
        assert isinstance(self._tree, WikiBulletTree), self._tree
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


##  WikiTextTokenizerTester
##
class WikiTextTokenizerTester(WikiTextTokenizer):
    
    def __init__(self):
        WikiTextTokenizer.__init__(self)
        self._tokens = []
        return
    
    def handle_token(self, token):
        WikiTextTokenizer.handle_token(self, token)
        self._tokens.append(token)
        return
    
    def handle_char(self, c):
        self._tokens.append(c)
        return
    
    def run(self, text):
        self.feed_text(text)
        self.finish()
        return self._tokens

##  WikiTextParserTester
##
class WikiTextParserTester(WikiTextParser):
    
    def run(self, text):
        self.feed_text(text)
        self.finish()
        return self.get_root()

#assert 0,WikiTextTokenizerTester().run("&amp;<!-- feoi -->")
#assert 0,WikiTextParserTester().run("{|bunge\n|bonge||bange\n|}")


##  WPXMLParser
##
class WPXMLParser(object):
    
    def __init__(self):
        self._expat = ParserCreate()
        self._expat.StartElementHandler = self.start_element
        self._expat.EndElementHandler = self.end_element
        self._expat.CharacterDataHandler = self.handle_data
        self._titleok = self._textok = False
        self._narticles = 0
        return
    
    def parse(self, fp):
        self._expat.ParseFile(fp)
        return
        
    def start_element(self, name, attrs):
        if name == 'page':
            self._revision = 0
            self._titleok = False
        elif name == 'title':
            self._titleok = True
            self._title = u''
        elif name == 'revision':
            pass
        elif name == 'text':
            self._textok = True
            self._textparser = WikiTextParser()     
        return
    
    def end_element(self, name):
        if name == 'text':
            self._textparser.finish()
            self._textok = False
        elif name == 'revision':
            self.handle_revision(self._title, self._revision, self._textparser)
            self._revision += 1
        elif name == 'title':
            self._titleok = False
        elif name == 'page':
            pass
        return
    
    def handle_data(self, data):
        if self._textok:
            self._textparser.feed_text(data)
        elif self._titleok:
            self._title += data
        return

    def handle_revision(self, title, revision, textparser):
        if revision != 0: return
        tree = textparser.get_root()
        def f(x):
            if x is WikiToken.PAR:
                sys.stdout.write('\n')
            elif isinstance(x, WikiTree):
                for c in x:
                    f(c)
                if (isinstance(x, WikiPreTree) or
                    isinstance(x, WikiBulletTree) or
                    isinstance(x, WikiHeadlineTree)):
                    sys.stdout.write('\n')
            elif isinstance(x, unicode):
                sys.stdout.write(x.encode('utf'))
        f(tree)
        print
        return

# main
def main(argv):
    args = argv[1:] or ['-']
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
        p = WPXMLParser()
        p.parse(fp)
        fp.close()
    return 0

if __name__ == '__main__': sys.exit(main(sys.argv))
