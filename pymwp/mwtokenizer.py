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
class WikiToken(Token): pass

WikiToken.EOL = WikiToken('\n')
WikiToken.BLANK = WikiToken(' ')
WikiToken.BAR = WikiToken('|')
WikiToken.BARTOP = WikiToken('|')
WikiToken.EXCTOP = WikiToken('!')
WikiToken.KEYWORD_OPEN = WikiToken('[[')
WikiToken.KEYWORD_CLOSE = WikiToken(']]')
WikiToken.LINK_OPEN = WikiToken('[')
WikiToken.LINK_CLOSE = WikiToken(']')
WikiToken.SPECIAL_OPEN = WikiToken('{{')
WikiToken.SPECIAL_CLOSE = WikiToken('}}')
WikiToken.TABLE_OPEN = WikiToken('{|')
WikiToken.TABLE_CLOSE = WikiToken('|}')
WikiToken.TABLE_ROW = WikiToken('|-')
WikiToken.TABLE_CAPTION = WikiToken('|+')
WikiToken.TABLE_HEADER_SEP = WikiToken('!!')
WikiToken.TABLE_DATA_SEP = WikiToken('||')
WikiToken.HR = WikiToken('HR')
WikiToken.PAR = WikiToken('PAR')
WikiToken.PRE = WikiToken('PRE')
WikiToken.QUOTE2 = WikiToken('QUOTE2')
WikiToken.QUOTE3 = WikiToken('QUOTE3')
WikiToken.QUOTE5 = WikiToken('QUOTE5')
WikiToken.COMMENT_OPEN = WikiToken('COMMENT_OPEN')
WikiToken.COMMENT_CLOSE = WikiToken('COMMENT_CLOSE')
    
class WikiVarToken(WikiToken):

    def __init__(self, name=u'', pos=0):
        Token.__init__(self, name)
        self.pos = pos
        return
    
class WikiHeadlineToken(WikiVarToken): pass
class WikiItemizeToken(WikiVarToken): pass
    

##  XMLTagToken
##
class XMLTagToken(Token):
    
    def __init__(self, name=u'', pos=0):
        Token.__init__(self, name)
        self.pos = pos
        return
    
class XMLStartTagToken(XMLTagToken):
    
    def __init__(self, name=u'', pos=0):
        XMLTagToken.__init__(self, name=name, pos=pos)
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

    class XMLEntityContext1(object):
        
        def __init__(self, pos, handler, state):
            self.pos = pos
            self.handler = handler
            self.state = state
            self.name = u''
            return

        def handle_char(self, c):
            self.handler(c)
            return

    class XMLEntityContext2(XMLEntityContext1):
            
        def handle_char(self, c):
            self.handler(self.pos, c)
            return

    def __init__(self, codec='utf-8'):
        self.codec = codec
        self._scan = self._scan_bol
        self._wiki = True
        self._token = None
        self._entity = None
        self._line_token = None
        self._quote_close = None
        self._pos = 0
        self._textpos = self._text = None
        return

    def close(self):
        if self._text is not None:
            self.handle_text(self._textpos, self._text)
            self._textpos = self._text = None
        return

    def feed_file(self, fp):
        self._lineno = 0
        for line in fp:
            line = line.decode(self.codec)
            self.feed_text(line)
            self._lineno += 1
        return

    def feed_text(self, text):
        i = 0
        while 0 <= i and i < len(text):
            i = self._scan(i, text[i])
            assert i is not None
        self._pos += len(text)
        return

    def handle_token(self, pos, token):
        return
    def handle_text(self, pos, text):
        return

    def _handle_token(self, i, token):
        pos = self._pos + i
        if self._text is not None:
            self.handle_text(self._textpos, self._text)
            self._textpos = self._text = None
        if (isinstance(token, XMLTagToken) and
            token.name == 'nowiki'):
            self._wiki = False
        elif (isinstance(token, XMLTagToken) and
              token.name == '/nowiki'):
            self._wiki = True
        self.handle_token(pos, token)
        return

    def _handle_char(self, i, c):
        if self._text is None:
            self._textpos = self._pos+i
            self._text = c
        else:
            self._text += c
        return

    def _scan_bol(self, i, c):
        self._line_token = None
        if c == '\n':
            self._handle_token(i, WikiToken.PAR)
            self._scan = self._scan_bol_nl
            return i+1
        elif c == '-':
            self._handle_token(i, WikiToken.HR)
            self._scan = self._scan_bol_hr
            return i+1
        elif c == '{':
            self._scan = self._scan_bol_brace
            return i+1
        elif c == '|':
            self._scan = self._scan_bol_bar
            return i+1
        elif c == '!':
            self._handle_token(i, WikiToken.EXCTOP)
            self._scan = self._scan_main
            return i+1
        elif c == '=':
            self._token = WikiHeadlineToken(pos=i)
            self._line_token = self._token
            self._scan = self._scan_bol_headline
            return i
        elif c in '*#:;':
            self._token = WikiItemizeToken(pos=i)
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
            self._handle_token(i, WikiToken.PRE)
            self._scan = self._scan_main
            return i

    def _scan_bol_hr(self, i, c):
        if c == '-':
            return i+1
        else:
            self._scan = self._scan_main
            return i
        
    def _scan_bol_brace(self, i, c):
        if c == '|':
            self._handle_token(i-1, WikiToken.TABLE_OPEN)
            self._scan = self._scan_main
            return i+1
        else:
            self._scan = self._scan_brace_open
            return i
        
    def _scan_bol_bar(self, i, c):
        if c == '}':
            self._handle_token(i-1, WikiToken.TABLE_CLOSE)
            self._scan = self._scan_main
            return i+1
        elif c == '+':
            self._handle_token(i-1, WikiToken.TABLE_CAPTION)
            self._scan = self._scan_main
            return i+1            
        elif c == '-':
            self._handle_token(i-1, WikiToken.TABLE_ROW)
            self._scan = self._scan_main
            return i+1            
        else:
            self._handle_token(i-1, WikiToken.BARTOP)
            self._scan = self._scan_main
            return i
    
    def _scan_bol_headline(self, i, c):
        assert isinstance(self._token, WikiHeadlineToken), self._token
        if c == '=':
            self._token.add_char(c)
            return i+1
        else:
            self._handle_token(self._token.pos, self._token)
            self._token = None
            self._scan = self._scan_main
            return i

    def _scan_bol_itemize(self, i, c):
        assert isinstance(self._token, WikiItemizeToken), self._token
        if c in '*#:;':
            self._token.add_char(c)
            return i+1
        else:
            self._handle_token(self._token.pos, self._token)
            self._token = None
            self._scan = self._scan_main
            return i

    def _scan_main(self, i, c):
        assert self._token is None, self._token
        if c == '&':
            self._entity = self.XMLEntityContext2(
                i,
                self._handle_char,
                self._scan_main)
            self._scan = self._scan_entity
            return i+1
        elif c == '<':
            self._scan = self._scan_tag
            return i+1
        elif not self._wiki:
            self._handle_char(i, c)
            return i+1
        elif c == '\n':
            self._handle_token(i, WikiToken.EOL)
            self._scan = self._scan_bol
            return i+1
        elif c.isspace():
            self._handle_token(i, WikiToken.BLANK)
            self._scan = self._scan_blank
            return i+1
        elif c == '|':
            self._scan = self._scan_bar
            return i+1
        elif c == '!':
            self._scan = self._scan_exc
            return i+1
        elif (c == '=' and
              isinstance(self._line_token, WikiHeadlineToken)):
            self._handle_token(i, self._line_token)
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
        else:
            self._handle_char(i, c)
            return i+1

    def _scan_headline_end(self, i, c):
        if c == '=':
            return i+1
        else:
            self._scan = self._scan_main
            return i
        
    def _scan_blank(self, i, c):
        if c == '\n':
            self._handle_token(i, WikiToken.EOL)
            self._scan = self._scan_bol
            return i+1
        elif c.isspace():
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
                self._entity.handle_char(unichr(n))
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
                self._entity.handle_char(unichr(n))
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
                self._entity.handle_char(unichr(n))
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
            self._handle_token(i-1, WikiToken.COMMENT_OPEN)
            self._scan = self._scan_comment
            return i+1
        elif c == '/':
            self._token = XMLEndTagToken(pos=i-1)
            self._scan = self._scan_endtag
            return i
        else:
            self._token = XMLStartTagToken(pos=i-1)
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
            self._handle_token(self._token.pos, self._token)
            self._token = None
            self._scan = self._scan_main
            return i+1
        else:
            return i+1

    def _scan_starttag_mid(self, i, c):
        assert isinstance(self._token, XMLStartTagToken), self._token
        if c == '>':
            self._handle_token(self._token.pos, self._token)
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
            self._entity = self.XMLEntityContext1(
                i,
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
            self._entity = self.XMLEntityContext1(
                i,
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
            self._handle_token(self._token.pos, self._token)
            self._token = None
            self._scan = self._scan_main
            return i+1
        elif c.isspace():
            return i+1
        else:
            self._token.add_char(c)
            return i+1

    def _scan_comment(self, i, c):
        if c == '>':
            self._handle_token(i, WikiToken.COMMENT_CLOSE)
            self._scan = self._scan_main
            return i+1
        elif c == '-':
            self._scan = self._scan_comment_h1
            return i+1
        else:
            self._handle_char(i, c)
            return i+1

    def _scan_comment_h1(self, i, c):
        if c == '-':
            self._scan = self._scan_comment_h2
            return i+1
        else:
            self._handle_char(i-1, u'-')
            self._scan = self._scan_comment
            return i

    def _scan_comment_h2(self, i, c):
        if c == '-':
            self._scan = self._scan_comment_h3
            return i+1
        else:
            self._handle_char(i, c)
            return i+1

    def _scan_comment_h3(self, i, c):
        if c == '-':
            self._scan = self._scan_comment
            return i+1
        else:
            self._handle_char(i-1, u'-')
            self._scan = self._scan_comment_h2
            return i

    def _scan_bracket_open(self, i, c):
        if c == '[':
            self._handle_token(i-1, WikiToken.KEYWORD_OPEN)
            self._scan = self._scan_main
            return i+1
        else:
            self._handle_token(i-1, WikiToken.LINK_OPEN)
            self._scan = self._scan_main
            return i

    def _scan_bracket_close(self, i, c):
        if c == ']':
            self._handle_token(i-1, WikiToken.KEYWORD_CLOSE)
            self._scan = self._scan_main
            return i+1
        else:
            self._handle_token(i-1, WikiToken.LINK_CLOSE)
            self._scan = self._scan_main
            return i

    def _scan_brace_open(self, i, c):
        if c == '{':
            self._handle_token(i-1, WikiToken.SPECIAL_OPEN)
            self._scan = self._scan_main
            return i+1
        else:
            self._handle_char(i-1, u'{')
            self._scan = self._scan_main
            return i

    def _scan_brace_close(self, i, c):
        if c == '}':
            self._handle_token(i-1, WikiToken.SPECIAL_CLOSE)
            self._scan = self._scan_main
            return i+1
        else:
            self._handle_char(i-1, u'}')
            self._scan = self._scan_main
            return i

    def _scan_q1(self, i, c):
        if c == "'":
            self._scan = self._scan_q2
            return i+1
        else:
            self._handle_char(i-1, u"'")
            self._scan = self._scan_main
            return i
    
    def _scan_q2(self, i, c):
        if c == "'":
            self._scan = self._scan_q3
            return i+1
        else:
            self._handle_token(i-1, WikiToken.QUOTE2)
            self._scan = self._scan_main
            return i
    
    def _scan_q3(self, i, c):
        if c == "'":
            self._scan = self._scan_q4
            return i+1
        else:
            self._handle_token(i-2, WikiToken.QUOTE3)
            self._scan = self._scan_main
            return i

    def _scan_q4(self, i, c):
        if c == "'":
            self._handle_token(i-4, WikiToken.QUOTE5)
            self._scan = self._scan_main
            return i+1
        else:
            # XXX what to do for 4 quotes? ('''')
            self._scan = self._scan_main
            return i

    def _scan_bar(self, i, c):
        if c == '|':
            self._handle_token(i-1, WikiToken.TABLE_DATA_SEP)
            self._scan = self._scan_main
            return i+1
        else:
            self._handle_token(i-1, WikiToken.BAR)
            self._scan = self._scan_main
            return i

    def _scan_exc(self, i, c):
        if c == '!':
            self._handle_token(i-1, WikiToken.TABLE_HEADER_SEP)
            self._scan = self._scan_main
            return i+1
        else:
            self._handle_char(i-1, u'!')
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
    
    def handle_text(self, text):
        self._tokens.append(text)
        return
    
    def run(self, text):
        self.feed_text(text)
        self.close()
        return self._tokens


# main
def main(argv):
    args = argv[1:] or ['-']
    class Tokenizer(WikiTextTokenizer):
        def handle_text(self, pos, text):
            print pos, repr(text)
            return
        def handle_token(self, pos, token):
            print pos, repr(token)
            return
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
        tokenizer = Tokenizer()
        for line in fp:
            line = unicode(line, codec)
            tokenizer.feed_text(line)
        fp.close()
        tokenizer.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
