#!/usr/bin/env python2
import sys
from htmlentitydefs import name2codepoint


##  Token
##
class Token(object):
    
    def __init__(self, name):
        self.name = name
        return
    
    def __repr__(self):
        return ('<%s %s>' %
                (self.__class__.__name__, self.name))
    
    def add_char(self, c):
        self.name += c
        return


##  WikiToken
##
class WikiToken(Token):

    def __init__(self, name=u''):
        Token.__init__(self, name)
        return

WikiToken.EOL = WikiToken('EOL')
WikiToken.BLANK = WikiToken('BLANK')
WikiToken.PAR = WikiToken('PAR')
WikiToken.PRE = WikiToken('PRE')
WikiToken.HR = WikiToken('HR')
WikiToken.QUOTE2 = WikiToken('QUOTE2')
WikiToken.QUOTE3 = WikiToken('QUOTE3')
WikiToken.QUOTE5 = WikiToken('QUOTE5')
WikiToken.BAR = WikiToken('BAR')
WikiToken.COMMENT_OPEN = WikiToken('COMMENT_OPEN')
WikiToken.COMMENT_CLOSE = WikiToken('COMMENT_CLOSE')
WikiToken.KEYWORD_OPEN = WikiToken('KEYWORD_OPEN')
WikiToken.KEYWORD_CLOSE = WikiToken('KEYWORD_CLOSE')
WikiToken.LINK_OPEN = WikiToken('LINK_OPEN')
WikiToken.LINK_CLOSE = WikiToken('LINK_CLOSE')
WikiToken.SPECIAL_OPEN = WikiToken('SPECIAL_OPEN')
WikiToken.SPECIAL_CLOSE = WikiToken('SPECIAL_CLOSE')
WikiToken.TABLE_OPEN = WikiToken('TABLE_OPEN')
WikiToken.TABLE_CLOSE = WikiToken('TABLE_CLOSE')
WikiToken.TABLE_ROW = WikiToken('TABLE_ROW')
WikiToken.TABLE_CAPTION = WikiToken('TABLE_CAPTION')
WikiToken.TABLE_HEADER = WikiToken('TABLE_HEADER')
WikiToken.TABLE_HEADER_SEP = WikiToken('TABLE_HEADER_SEP')
WikiToken.TABLE_DATA = WikiToken('TABLE_DATA')
WikiToken.TABLE_DATA_SEP = WikiToken('TABLE_DATA_SEP')
    
class WikiHeadlineToken(WikiToken): pass
class WikiItemizeToken(WikiToken): pass
    

##  XMLTagToken
##
class XMLTagToken(Token):
    
    def __init__(self, name=u''):
        Token.__init__(self, name)
        return
    
class XMLStartTagToken(XMLTagToken):
    
    def __init__(self):
        XMLTagToken.__init__(self)
        self._attrs = []
        self._key = self._value = None
        return
    
    def __repr__(self):
        return ('<%s %r%s>' %
                (self.__class__.__name__, self.name,
                 ''.join( ' %r=%r' % (k,v) for (k,v) in self._attrs )))
    
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
            self._attrs.append((self._key, self._key))
        else:
            self._attrs.append((self._key, self._value))
        self._key = self._value = None
        return

class XMLEndTagToken(XMLTagToken):

    def __repr__(self):
        return ('<%s %r>' %
                (self.__class__.__name__, self.name))

    
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

    def close(self):
        return

    def feed_file(self, fp):
        for line in fp:
            self.feed_text(line)
        return

    def feed_text(self, text):
        i = 0
        while 0 <= i and i < len(text):
            i = self._scan(i, text[i])
            assert i is not None
        return

    def handle_token(self, token):
        if (isinstance(token, XMLTagToken) and
            token.name == 'nowiki'):
            self._wiki = False
        elif (isinstance(token, XMLTagToken) and
              token.name == '/nowiki'):
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
            self._token = WikiItemizeToken()
            self._line_token = self._token
            self._scan = self._scan_bol_itemize
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

    def _scan_bol_itemize(self, i, c):
        assert isinstance(self._token, WikiItemizeToken), self._token
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
            self._entity = self.XMLEntityContext(
                self.handle_char,
                self._scan_main)
            self._scan = self._scan_entity
            return i+1
        elif c == '<':
            self._scan = self._scan_tag
            return i+1
        elif not self._wiki:
            self.handle_char(c)
            return i+1
        elif c == '\n':
            self.handle_token(WikiToken.EOL)
            self._line_token = None
            self._scan = self._scan_bol
            return i+1
        elif c.isspace():
            self.handle_token(WikiToken.BLANK)
            self._scan = self._scan_blank
            return i+1
        elif (c == '|' and
              self._line_token is WikiToken.TABLE_DATA):
            self._scan = self._scan_bar
            return i+1
        elif (c == '!' and
              self._line_token is WikiToken.TABLE_DATA):
            self._scan = self._scan_exc
            return i+1
        elif (c == '=' and
              isinstance(self._line_token, WikiHeadlineToken)):
            self.handle_token(self._line_token)
            self._scan = self._scan_headline_end
            return i
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
        elif c == '|':
            self.handle_token(WikiToken.BAR)
            return i+1
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
        if c.isalnum():
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
            self._token.add_char(c)
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
            self._entity = self.XMLEntityContext(
                self._add_value_char,
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
            self._entity = self.XMLEntityContext(
                self._add_value_char,
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
        # XXX not handling "--"
        if c == '>':
            self.handle_token(WikiToken.COMMENT_CLOSE)
            self._scan = self._scan_main
            return i+1
        else:
            self.handle_char(c)
            return i+1

    def _scan_bracket_open(self, i, c):
        if c == '[':
            self.handle_token(WikiToken.KEYWORD_OPEN)
            self._scan = self._scan_main
            return i+1
        else:
            self.handle_token(WikiToken.LINK_OPEN)
            self._scan = self._scan_main
            return i

    def _scan_bracket_close(self, i, c):
        if c == ']':
            self.handle_token(WikiToken.KEYWORD_CLOSE)
            self._scan = self._scan_main
            return i+1
        else:
            self.handle_token(WikiToken.LINK_CLOSE)
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
        self.close()
        return self._tokens


# main
def main(argv):
    args = argv[1:] or ['-']
    class Tokenizer(WikiTextTokenizer):
        def handle_char(self, c):
            print repr(c)
            return
        def handle_token(self, token):
            print repr(token)
            return
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
        tokenizer = Tokenizer()
        for line in fp:
            line = unicode(line, codec)
            tokenizer.feed_text(line)
        fp.close()
        tokenizer.close()
        print
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
