from enum import Enum, unique


@unique
class TokenType(Enum):
    # Special Symbols come from 6.1.2 in the ISO standard
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
    IDIV = 'div'  # named to avoid confusion with DIVIDE
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

    # Directives are defined in 6.1.4. of the ISO standard.  "forward" is the only directive defined.
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

    # Commentary (comments) defined in 6.1.8 of the ISO Standard.  TO-DO: Describe why we are defining
    # a comment token but not { or } as tokens.
    COMMENT = 'comment'

    # TODO: Alternative Representations in 6.1.9 - we will do later

    # Ordinal Types are defined in section 6.4.2.2 in the ISO Standard
    INTEGER = 'integer'
    REAL = 'real'
    BOOLEAN = 'Boolean'
    TRUE = 'true'
    FALSE = 'false'
    CHAR = 'char'
    # "string" is technically not a required identifier, but we are supporting it in this implementation
    STRING = 'string'

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

    # Invalid Tokens may be seen during lexing, but we do not want to stop lexing at the first invalid
    # token.  So, we would store the invalid token and raise an error during parsing.
    INVALID_TOKEN = 'invalid token'

    def __str__(self):
        return self.value


class Token:
    def __init__(self, tokentype, line, column, filename, value):
        self.tokentype = tokentype
        self.line = line
        self.column = column
        self.filename = filename
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

    def __str__(self):
        return '{0:<18} val:{1:<15} file:{2:<15} l:{3:<5} c:{4:<3}\n'.format(self.tokentype, self.value,
                                                                             self.filename, self.line,
                                                                             self.column)


class TokenStream:
    def __init__(self):
        self.tokenlist = []
        self.pos = 0

    def addtoken(self, token):
        if not isinstance(token, Token):
            raise TypeError("Only Tokens may be added to TokenStream")
        self.tokenlist.append(token)

    def __iter__(self):
        self.pos = 0
        return self

    def peektoken(self):
        # returns the next token in the token list, but does not advance the position.  Used
        # when interpretation of a token varies based on the token that follows.
        # returns None if we are past the end of the token list.
        try:
            ret = self.tokenlist[self.pos]
        except IndexError:
            ret = None
        return ret

    def __next__(self):
        # consumes the next token off the token list, by moving the position to the next step.
        # if we are past the end of the token list, return None
        try:
            ret = self.tokenlist[self.pos]
            self.pos += 1
        except IndexError:
            raise StopIteration
        return ret


class Lexer:
    def __init__(self, filename):
        self.filename = filename
        self.tokenstream = TokenStream()
        self.text = ""
        self.length = 0
        self.curpos = 0
        self.line = 1
        self.column = 1

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
        if pos >= self.length:
            return ""
        else:
            return self.text[pos]

    def peekmulti(self, num):
        return self.text[self.curpos:self.curpos + num]

    def eat(self):
        if self.at_eof():
            raise IndexError("Length Exceeded")
        else:
            ret = self.text[self.curpos]
            self.curpos += 1
            if ret == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            return ret

    def eatwhitespace(self):
        while self.peek().isspace():
            self.eat()

    def eatidentifier(self):
        # Definition of identifier in section 6.1.3 of ISO Standard is letter { letter | digit } .
        # This function validates that the next character in the input string is a letter, and if so,
        # returns the identifier.  Returns empty string if the next character in the input string
        # is not alphabetic.
        ret = ""
        if self.peek().isalpha():
            ret = self.eat()
            while self.peek().isalnum():
                ret += self.eat()
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
        # Returns empty string if the next character in the input string is not numeric.
        ret = ""
        while self.peek().isnumeric():
            ret += self.eat()
            if self.peek() == '.':
                if self.peekahead(1).isnumeric():
                    ret += self.eat()  # grab the period
                    while self.peek().isnumeric():
                        ret += self.eat()
                else:
                    # Cannot end a number with a period and no digits following.  Nor is there any other valid
                    # token that could start with a period and follow a number.
                    raise ValueError("Invalid character '.'")
            if self.peek().lower() == 'e':
                if self.peekahead(1) in ['+', '-'] and self.peekahead(2).isnumeric():
                    ret += self.eat()  # grab the 'e'
                    ret += self.eat()  # grab the sign
                    while self.peek().isnumeric():
                        ret += self.eat()
                elif self.peekahead(1).isnumeric():
                    ret += self.eat()  # grab the 'e'
                    while self.peek().isnumeric():
                        ret += self.eat()
                else:
                    errstr = "Invalid character '{}'".format(self.peek())
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
                    self.eat()
                    self.eat()  # eat both apostrophes
                elif self.peek() == "'":
                    self.eat()  # eat the closing apostrophe
                    done = True
                else:
                    try:
                        ret += self.eat()
                    except IndexError:
                        print("Unterminated character string")
                        raise
        return ret

    def lex(self):
        if self.filename == "":
            print("Filename not set, cannot Tokenize")
            return
        try:
            f = open(self.filename, "r")
            self.text = f.read()
            self.length = len(self.text)
            f.close()
        except FileNotFoundError:
            print("Invalid filename: {}".format(self.filename))
            return

        # TODO: Finish the tokenization
        while not self.at_eof():
            self.eatwhitespace()
            # remember where this next token starts, since that is the position a user would want to see
            startline = self.line
            startcolumn = self.column
            try:
                if self.peek() == "'":
                    val = self.eatcharacterstring()
                    self.tokenstream.addtoken(Token(TokenType.CHARSTRING, startline, startcolumn, self.filename, val))
                elif self.peek().isalpha():
                    val = self.eatidentifier()
                    self.tokenstream.addtoken(Token(TokenType.IDENTIFIER, startline, startcolumn, self.filename, val))
                elif self.peek().isnumeric():
                    # could be a real or an integer.  Read until the next non-numeric character.  If that character
                    # is an e, E, or . then it is a real, else it is an integer.
                    lookahead = 1
                    while self.peekahead(lookahead).isnumeric():
                        lookahead += 1
                    if self.peekahead(lookahead) == '.' or self.peekahead(lookahead).lower() == 'e':
                        val = self.eatrealnumber()
                        self.tokenstream.addtoken(Token(TokenType.UNSIGNED_REAL, startline, startcolumn,
                                                        self.filename, val))
                    else:
                        val = ""
                        while self.peek().isnumeric():
                            val += self.eat()
                        self.tokenstream.addtoken(Token(TokenType.UNSIGNED_INT, startline, startcolumn,
                                                        self.filename, val))
            except Exception:
                print("Parse error in {} at line: {}, column: {}".format(self.filename, startline, startcolumn))
                raise

        for i in self.tokenstream:
            print(i)
