from enum import Enum, unique
from copy import copy
from filelocation import FileLocation
from editor_settings import NUM_SPACES_IN_TAB


class LexerException(Exception):
    pass


@unique
class TokenType(Enum):
    # Special Symbols come from 6.1.2 in the ISO standard.  Section 6.1.9 of the
    # standard specifies some alternate representations for symnbols.  We will
    # handle those via a lookup mapping later.
    PLUS = '+'
    MINUS = "-"
    MULTIPLY = '*'
    DIVIDE = '/'
    EQUALS = '='
    LESS = '<'
    GREATER = '>'
    LBRACKET = '['
    RBRACKET = ']'
    PERIOD = '.'
    COMMA = ','
    COLON = ':'
    SEMICOLON = ';'
    POINTER = '^'
    LPAREN = '('
    RPAREN = ')'
    NOTEQUAL = "<>"
    LESSEQ = "<="
    GREATEREQ = ">="
    ASSIGNMENT = ":="
    SUBRANGE = ".."

    # Reserved Words come from 6.1.2 in the ISO standard
    AND = 'and'
    ARRAY = 'array'
    BEGIN = 'begin'
    CASE = 'case'
    CONST = 'const'
    IDIV = 'div'  # named IDIV to avoid confusion with DIVIDE
    DO = 'do'
    DOWNTO = 'downto'
    ELSE = 'else'
    END = 'end'
    FILE = 'file'
    FOR = 'for'
    FUNCTION = 'function'
    GOTO = 'goto'
    IF = 'if'
    IN = 'in'
    LABEL = 'label'
    MOD = 'mod'
    NIL = 'nil'
    NOT = 'not'
    OF = 'of'
    OR = 'or'
    PACKED = 'packed'
    PROCEDURE = 'procedure'
    PROGRAM = 'program'
    RECORD = 'record'
    REPEAT = 'repeat'
    SET = 'set'
    THEN = 'then'
    TO = 'to'
    TYPE = 'type'
    UNTIL = 'until'
    VAR = 'var'
    WHILE = 'while'
    WITH = 'with'

    # Identifiers are defined in 6.1.3 of the ISO Standard
    IDENTIFIER = 'ident'

    # Directives are defined in 6.1.4. of the ISO standard.
    # "forward" is the only directive defined.
    FORWARD = 'forward'

    # Numbers are defined in 6.1.5 of the ISO Standard
    SIGNED_REAL = 'signed real'
    UNSIGNED_REAL = 'unsigned real'
    SIGNED_INT = 'signed int'
    UNSIGNED_INT = 'unsigned int'

    # Label is defined in 6.1.6 of the ISO Standard
    LABELID = 'label identifier'

    # Character Strings are defined in 6.1.7 of the ISO Standard
    CHARSTRING = 'character string'

    # Ordinal Types are defined in section 6.4.2.2 in the ISO Standard
    INTEGER = 'integer'
    REAL = 'real'
    BOOLEAN = 'Boolean'
    TRUE = 'true'
    FALSE = 'false'
    CHAR = 'char'

    # File types are defined in section 6.4.3.5 of the ISO standard
    TEXT = 'text'

    # Most of the required procedures in 6.6.5 of the ISO standard are going to need to be handled by the compiler.
    # File Handling Procedures are defined in 6.6.5.2
    REWRITE = 'rewrite'
    PUT = 'put'
    RESET = 'reset'
    GET = 'get'
    # Read() and Write() can be defined in terms of Get() and Put().  However, since these functions
    # are variadic (they can have variable-length parameter lists) and are the only Pascal functions
    # with this property, handling them in the compiler will be easier.
    READ = 'read'
    WRITE = 'write'
    # readln() is defined in 6.9.2
    READLN = 'readln'
    # writeln() is defined in 6.9.4
    WRITELN = 'writeln'

    # Dynamic Allocation Procedures are defined in 6.6.5.3 of the ISO Standard
    NEW = 'new'
    DISPOSE = 'dispose'

    # Transfer Procedures are defined in 6.6.5.4 of the ISO Standard
    PACK = 'pack'
    UNPACK = 'unpack'

    # For the required functions in 6.6.6 of the ISO Standard, some could be handled outside the compiler, but
    # for now, we will handle them in the compiler.  As a note, this will prevent overriding the definitions,
    # compared to writing these in Pascal in a Unit that could be optionally included.
    # Arithmetic Functions are defined in 6.6.6.2
    ABS = 'abs'
    SQR = 'sqr'
    SIN = 'sin'
    COS = 'cos'
    EXP = 'exp'
    LN = 'ln'
    SQRT = 'sqrt'
    ARCTAN = 'arctan'

    # Transfer Functions are defined in 6.6.6.3 of the ISO Standard
    TRUNC = 'trunc'
    ROUND = 'round'

    # Ordinal Functions are defined in 6.6.6.4 of the ISO Standard
    ORD = 'ord'
    CHR = 'chr'
    SUCC = 'succ'
    PRED = 'pred'

    # Boolean Functions are defined in 6.6.6.5 of the ISO Standard
    ODD = 'odd'
    EOF = 'eof'
    EOLN = 'eoln'

    # Required Constant is defined in 6.7.2.2 of the ISO Standard
    MAXINT = 'maxint'

    # The required procedure "page" is defined in section 6.9.5 of the ISO standard
    PAGE = 'page'

    # Program Parameters are defined in section 6.10 of the ISO Standard
    INPUT = 'input'
    OUTPUT = 'output'

    # Empty Statements do not have a token, but for some special cases, I need an AST that is a NOOP.
    EMPTYTOKEN = None

    def __str__(self):
        if self.value is not None:
            return self.value
        else: # pragma: no cover
            return 'EMPTY TOKEN'


# To make it easy to lex various tokens, we can use a lookup from the reserved words back to the
# TokenTypes we just defined to eliminate the need for a long if/elif block testing for each word.
# Note, not all TokenTypes map to reserved words.  Example: TokenType.IDENTIFIER or TokenType.SIGNED_REAL.

TOKENTYPE_LOOKUP = {
    'abs': TokenType.ABS, 'and': TokenType.AND,
    'arctan': TokenType.ARCTAN, 'array': TokenType.ARRAY, 'begin': TokenType.BEGIN,
    'boolean': TokenType.BOOLEAN, 'case': TokenType.CASE, 'chr': TokenType.CHR, 'char': TokenType.CHAR,
    'const': TokenType.CONST, 'cos': TokenType.COS,
    'dispose': TokenType.DISPOSE, 'div': TokenType.IDIV, 'do': TokenType.DO, 'downto': TokenType.DOWNTO,
    'else': TokenType.ELSE, 'end': TokenType.END, 'eof': TokenType.EOF, 'eoln': TokenType.EOLN,
    'exp': TokenType.EXP, 'false': TokenType.FALSE, 'file': TokenType.FILE, 'for': TokenType.FOR,
    'forward': TokenType.FORWARD, 'function': TokenType.FUNCTION,
    'get': TokenType.GET, 'goto': TokenType.GOTO, 'if': TokenType.IF, 'in': TokenType.IN,
    'input': TokenType.INPUT, 'integer': TokenType.INTEGER,
    'label': TokenType.LABEL, 'ln': TokenType.LN, 'maxint': TokenType.MAXINT, 'mod': TokenType.MOD,
    'new': TokenType.NEW, 'nil': TokenType.NIL, 'not': TokenType.NOT, 'odd': TokenType.ODD, 'of': TokenType.OF,
    'or': TokenType.OR, 'ord': TokenType.ORD, 'output': TokenType.OUTPUT,
    'pack': TokenType.PACK, 'packed': TokenType.PACKED,
    'page': TokenType.PAGE, 'pred': TokenType.PRED, 'procedure': TokenType.PROCEDURE,
    'program': TokenType.PROGRAM, 'put': TokenType.PUT, 'read': TokenType.READ, 'readln': TokenType.READLN,
    'real': TokenType.REAL, 'record': TokenType.RECORD, 'repeat': TokenType.REPEAT,
    'reset': TokenType.RESET, 'rewrite': TokenType.REWRITE, 'round': TokenType.ROUND,
    'sin': TokenType.SIN, 'set': TokenType.SET, 'sqr': TokenType.SQR, 'sqrt': TokenType.SQRT,
    'succ': TokenType.SUCC,
    'text': TokenType.TEXT, 'then': TokenType.THEN, 'to': TokenType.TO, 'trunc': TokenType.TRUNC,
    'true': TokenType.TRUE, 'type': TokenType.TYPE, 'unpack': TokenType.UNPACK,
    'until': TokenType.UNTIL, 'var': TokenType.VAR, 'while': TokenType.WHILE, 'with': TokenType.WITH,
    'write': TokenType.WRITE, 'writeln': TokenType.WRITELN
}


# Similar lookup for symbols.  Note that there are alternate representations for brackets and
# the pointer symbol defined in section 6.1.9 of the ISO Standard.
SYMBOL_LOOKUP = {
    ':=': TokenType.ASSIGNMENT, ':': TokenType.COLON,
    ',': TokenType.COMMA, '/': TokenType.DIVIDE,
    '=': TokenType.EQUALS, '>': TokenType.GREATER,
    '>=': TokenType.GREATEREQ, '[': TokenType.LBRACKET,
    '(.': TokenType.LBRACKET, '<': TokenType.LESS,
    '<=': TokenType.LESSEQ, '(': TokenType.LPAREN,
    '-': TokenType.MINUS, '*': TokenType.MULTIPLY,
    '<>': TokenType.NOTEQUAL, '.': TokenType.PERIOD,
    '+': TokenType.PLUS, '^': TokenType.POINTER,
    '@': TokenType.POINTER, ']': TokenType.RBRACKET,
    '.)': TokenType.RBRACKET, ')': TokenType.RPAREN,
    ';': TokenType.SEMICOLON, '..': TokenType.SUBRANGE
}


class Token:
    def __init__(self, tokentype, location, value):
        self.tokentype = tokentype
        self.location = location
        self.value = value

    # Use a property for tokentype so we can enforce that it is always a valid TokenType
    @property
    def tokentype(self):
        return self.__tokentype

    @tokentype.setter
    def tokentype(self, t):
        if isinstance(t, TokenType):
            self.__tokentype = t
        else:  # pragma: no cover
            raise TypeError("Invalid Token Type")

    def __str__(self): # pragma: no cover
        return '{0:<18} val: {1:<15} {2:<35}\n'.format(self.tokentype, self.value, str(self.location))


class TokenStream:
    def __init__(self):
        self.tokenlist = []
        self.pos = 0
        # TODO - see if we can do something with slices here.
        self.printstartpos = []
        self.printendpos = []

    def setstartpos(self):
        self.printstartpos.append(self.pos)

    def setendpos(self):
        self.printendpos.append(self.pos)

    def printstarttoend(self):
        # TODO - there is a more pythonic way of doing this I am certain
        ret = ""
        start = self.printstartpos[-1]
        end = self.printendpos[-1]

        i = start
        while i < end:
            if self.tokenlist[i].tokentype == TokenType.CHARSTRING:
                ret += "'" + self.tokenlist[i].value + "'"
            else:
                ret += self.tokenlist[i].value
            ret += " "
            i += 1
        del self.printstartpos[-1]
        del self.printendpos[-1]
        return ret

    def addtoken(self, token):
        assert isinstance(token, Token), "Only Tokens may be added to TokenStream"
        self.tokenlist.append(token)

    # One can iterate over a TokenStream if desired, primarily for debugging purposes
    # (e.g. printing out all the tokens in the stream)
    def __iter__(self): # pragma: no cover
        self.pos = 0
        return self

    def __next__(self): # pragma: no cover
        try:
            ret = self.tokenlist[self.pos]
            self.pos += 1
        except IndexError:
            raise StopIteration
        return ret

    def resetpos(self):
        self.pos = 0

    def eattoken(self):
        from compiler_error import compiler_errstr
        try:
            ret = self.tokenlist[self.pos]
        except IndexError:
            if self.pos > 0:
                raise LexerException(compiler_errstr("Missing 'end' statement or Unexpected end of file", self.tokenlist[self.pos - 1]))
            else:
                raise LexerException(compiler_errstr("Cannot compile empty file"))
        self.pos += 1
        return ret

    def peekprevioustoken(self):
        if self.pos > 0:
            return self.tokenlist[self.pos - 1]
        else: # pragma: no cover
            return None

    def peektoken(self):
        from compiler_error import compiler_errstr
        try:
            ret = self.tokenlist[self.pos]
        except IndexError: # pragma: no cover
            if self.pos > 0:
                raise LexerException(compiler_errstr("Unexpected end of file", self.tokenlist[self.pos - 1]))
            else:
                raise LexerException("Unexpected end of file")
        assert isinstance(ret, Token)
        return ret

    def peektokentype(self):
        # returns the type of the next token in the token list, but does not advance the position.  Used
        # when interpretation of a token varies based on the token that follows.
        # returns None if we are past the end of the token list.
        try:
            ret = self.tokenlist[self.pos].tokentype
        except IndexError:
            ret = None
        return ret

    def peekmultitokentype(self, num):
        # returns a list of the types of the next num tokens in the token list, but does not advance the position.
        # Used when interpretation of a token varies based on multiple tokens that follow.  Returns the empty
        # list if we are past the end of the token list.  If we are not past the end of the token list, but there
        # are fewer than num tokens left in the list, then will return all remaining tokens in the token list.

        ret = []
        i = self.pos
        try:
            while i < self.pos + num:
                ret.append(self.tokenlist[i].tokentype)
                i += 1
        except IndexError: # pragma: no cover
            pass
        return ret


class Lexer:
    def __init__(self, filename):
        self.tokenstream = TokenStream()
        self.text = ""
        self.length = 0
        self.curpos = 0
        self.location = FileLocation(filename, 1, 1, "")

    def at_eof(self):
        return self.curpos >= self.length

    def peek(self):
        # returns the next character in the input text, or "" if we are past the end of the input.
        if self.at_eof():
            return ""
        else:
            return self.text[self.curpos]

    def peekahead(self, num):
        # returns the character that is num characters ahead.  Passing 0 for num is synonymous with peek().
        assert (num >= 0), "Cannot peek behind current position"
        pos = self.curpos + num
        if pos < self.length:
            return self.text[pos]
        else: # pragma: no cover
            return ""

    def peekrestofcurrentline(self):
        # returns the text from the current position until the end of current line or end of file, whichever
        # comes first.
        i = 0
        while not self.at_eof() and self.text[self.curpos + i] != "\n":
            i += 1
        if i == 0:
            return ""
        else:
            return self.peekmulti(i)

    def peekmulti(self, num):
        return self.text[self.curpos:self.curpos + num]

    def eat(self):
        if self.at_eof(): # pragma: no cover
            raise IndexError("Length Exceeded")
        else:
            ret = self.text[self.curpos]
            self.curpos += 1
            if ret == '\n':
                self.location.line += 1
                self.location.column = 1
                self.location.curlinestr = self.peekrestofcurrentline()
            elif ret == '\t':
                self.location.column += NUM_SPACES_IN_TAB
            else:
                self.location.column += 1
            return ret

    def eatmulti(self, num):
        ret = ""
        for i in range(num):
            ret += self.eat()
        return ret

    def eatwhitespace(self):
        while self.peek().isspace():
            self.eat()

    def eatidentifier(self):
        # Definition of identifier in section 6.1.3 of ISO Standard is letter { letter | digit } .
        # This function validates that the next character in the input string is a letter, and if so,
        # returns the identifier.  Returns empty string if the next character in the input stream
        # is not alphabetic.
        ret = ""
        if self.peek().isalpha():
            ret = self.eat()
            while self.peek().isalnum():
                ret += self.eat()
        return ret

    def eatcomment(self):
        # Definition of commentary in section 6.1.8 of the ISO standard is
        # ( '{' | '(*' ) commentary ( '}' | '*)' ).  The actual commentary itself can be any arbitrary string of
        # characters, on multiple lines.  Comments do not nest, so the string "{ (* a comment *) }" is invalid, as the
        # comment ends on the *), so the } would be flagged as an invalid token.
        # Returns empty string if the next character(s) in the input stream is not a comment opening.
        assert self.peek() == '{' or self.peekmulti(2) == '(*'

        ret = ""
        if self.peek() == '{':
            self.eat()
        elif self.peekmulti(2) == '(*':
            self.eatmulti(2)

        while self.peek() != '}' and self.peekmulti(2) != '*)':
            ret += self.eat()
        if self.peek() == '}':
            self.eat()
        else:  # eat the *)
            self.eatmulti(2)
        return ret

    def eatrealnumber(self):
        # The lexer eats all signs as plus and minus tokens respectively, and relies on the parser to
        # transform into either a signed number or into another mathematical statement.  This function
        # reads any of the valid numerical forms and returns the string corresponding to them.
        # Relevant definitions from section 6.1.5 of the ISO Standard:
        #   unsigned-integer = digit-sequence .
        #   unsigned-real = digit-sequence '.' fractional-part ['e' scale-factor] |
        #                   digit-sequence 'e' scale-factor .
        #   fractional-part = digit-sequence .
        #   scale-factor = [sign] digit-sequence .
        #   digit-sequence = digit { digit } .
        #   digit = '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' .
        #
        # As a note, the 'e' in the unsigned-real can be lower or upper case.
        #
        # Returns empty string if the next character in the input stream is not numeric.
        ret = ""
        while self.peek().isnumeric():
            ret += self.eat()
            if self.peek() == '.':
                if self.peekahead(1).isnumeric():
                    ret += self.eat()  # grab the period
                    while self.peek().isnumeric():
                        ret += self.eat()
                else:
                    # Cannot end a real with a period and no digits following.
                    raise ValueError("Invalid character '.'")
            if self.peek().lower() == 'e':
                if self.peekahead(1) in ['+', '-'] and self.peekahead(2).isnumeric():
                    ret += self.eatmulti(2)  # grab the 'e' and the sign
                    while self.peek().isnumeric():
                        ret += self.eat()
                elif self.peekahead(1).isnumeric():
                    ret += self.eat()  # grab the 'e'
                    while self.peek().isnumeric():
                        ret += self.eat()
                else:
                    errstr = "Invalid real number format: {}".format(ret + self.peek())
                    raise ValueError(errstr)
        return ret

    def eatcharacterstring(self):
        # Note that since apostrophe is part of the BNF here, I will use quotes to indicate specific characters
        # for ease of readability.
        #
        # character-string = "'" string-element {string-element} "'"  .
        # string-element = apostrophe-image | string-character
        # apostrophe-image = "''"
        # string-character = one of a set of implementation-defined characters.  In this implementation we will accept
        #   any character that Python can handle.
        #
        # returns empty string if this is not a character string.  Else, returns the value of the string excluding
        # the opening and closing apostrophes, as they are not part of the actual value of the string.

        ret = ''
        if self.peek() == "'":
            self.eat()  # remove the apostrophe
            done = False
            while not done:
                if self.peekmulti(2) == "''":
                    ret += "'"  # add the single apostrophe
                    self.eatmulti(2)  # eat both apostrophes
                elif self.peek() == "'":
                    self.eat()  # eat the closing apostrophe
                    done = True
                else:
                    try:
                        ret += self.eat()
                    except IndexError:
                        raise LexerException("Unterminated character string")
        return ret

    def lex(self):
        from compiler_error import compiler_errstr

        assert self.location.filename != "", "Filename not set, cannot Tokenize"
        try:
            f = open(self.location.filename, "r")
            self.text = f.read()
            self.length = len(self.text)
            f.close()
            self.location.curlinestr = self.peekrestofcurrentline()
        except FileNotFoundError:
            raise LexerException("Invalid filename: {}".format(self.location.filename))

        self.eatwhitespace()
        while not self.at_eof():
            # Remember where this next token starts, since that is the position a user would want to see in an error
            # It needs to be a copy, else every token we create in every iteration would share the same location
            # object.
            curlocation = copy(self.location)
            try:
                if self.peek() == "'":
                    val = self.eatcharacterstring()
                    self.tokenstream.addtoken(Token(TokenType.CHARSTRING, curlocation, val))
                elif self.peek().isalpha():
                    val = self.eatidentifier()
                    if val.lower() in TOKENTYPE_LOOKUP.keys():
                        toktype = TOKENTYPE_LOOKUP[val.lower()]
                    else:
                        toktype = TokenType.IDENTIFIER
                    self.tokenstream.addtoken(Token(toktype, curlocation, val))
                elif self.peek().isnumeric():
                    # could be a real or an integer.  Read until the next non-numeric character.  If that character
                    # is an e, E, or a . followed by a digit then it is a real, else it is an integer.
                    lookahead = 1
                    while self.peekahead(lookahead).isnumeric():
                        lookahead += 1
                    if ((self.peekahead(lookahead) == '.' and self.peekahead(lookahead+1).isnumeric()) or
                            self.peekahead(lookahead).lower() == 'e'):
                        val = self.eatrealnumber()
                        self.tokenstream.addtoken(Token(TokenType.UNSIGNED_REAL, curlocation, val))
                    else:
                        val = ""
                        while self.peek().isnumeric():
                            val += self.eat()
                        self.tokenstream.addtoken(Token(TokenType.UNSIGNED_INT, curlocation, val))
                elif self.peek() == '{' or self.peekmulti(2) == '(*':
                    self.eatcomment()
                    # Comments are totally ignored from here forward, so we do not add those to the tokenstream.
                elif self.peek() in ['+', '-', '*', '/', '=', '<', '>', '[', ']', '.', ',', ':', ';',
                                     '^', '(', ')', '@']:
                    # Test first for the 2-character symbols, and if none of those match, we know
                    # we have a single-character symbol.
                    if self.peekmulti(2) in [':=', '>=', '<=', '<>', '(.', '.)', '..']:
                        val = self.eatmulti(2)
                    else:
                        val = self.eat()
                    toktype = SYMBOL_LOOKUP[val]
                    self.tokenstream.addtoken(Token(toktype, curlocation, val))
                else:
                    #errstr = compiler_errstr('Unexpected character: {}'.format(self.peek()), None, curlocation)
                    raise LexerException('Unexpected character: {}'.format(self.peek()))
            except Exception as e:
                raise LexerException(compiler_errstr(e, None, curlocation))

            self.eatwhitespace()
