from enum import Enum, unique
from copy import copy
from filelocation import FileLocation
from editor_settings import NUM_SPACES_IN_TAB


class LexerException(Exception):
    pass


@unique
class TokenType(Enum):
    # Special Symbols come from 6.1.2 in the ISO standard.  Section 6.1.9 of the
    # standard specifies some alternate representations for symbols.  We will
    # handle those via a lookup mapping later.
    PLUS = '+'
    MINUS = "-"
    MULTIPLY = '*'
    DIVIDE = '/'
    EQUALS = '='
    LESS = '<'
    GREATER = '>'
    LEFT_BRACKET = '['
    RIGHT_BRACKET = ']'
    PERIOD = '.'
    COMMA = ','
    COLON = ':'
    SEMICOLON = ';'
    POINTER = '^'
    LEFT_PAREN = '('
    RIGHT_PAREN = ')'
    NOTEQUAL = "<>"
    LESS_EQUAL = "<="
    GREATER_EQUAL = ">="
    ASSIGNMENT = ":="
    SUBRANGE = ".."

    # Reserved Words come from 6.1.2 in the ISO standard
    AND = 'and'
    ARRAY = 'array'
    BEGIN = 'begin'
    CASE = 'case'
    CONST = 'const'
    INTEGER_DIV = 'div'  # named INTEGER_DIV to avoid confusion with DIVIDE
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
    LABEL_IDENTIFIER = 'label identifier'

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
    EMPTY_TOKEN = None

    def __str__(self):
        if self.value is not None:
            return self.value
        else:  # pragma: no cover
            return 'EMPTY TOKEN'


# To make it easy to lex various tokens, we can use a lookup from the reserved words back to the
# TokenTypes we just defined to eliminate the need for a long if/elif block testing for each word.
# Note, not all TokenTypes map to reserved words.  Example: TokenType.IDENTIFIER or TokenType.SIGNED_REAL.

TOKEN_TYPE_LOOKUP = {
    'abs': TokenType.ABS, 'and': TokenType.AND,
    'arctan': TokenType.ARCTAN, 'array': TokenType.ARRAY, 'begin': TokenType.BEGIN,
    'boolean': TokenType.BOOLEAN, 'case': TokenType.CASE, 'chr': TokenType.CHR, 'char': TokenType.CHAR,
    'const': TokenType.CONST, 'cos': TokenType.COS,
    'dispose': TokenType.DISPOSE, 'div': TokenType.INTEGER_DIV, 'do': TokenType.DO, 'downto': TokenType.DOWNTO,
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
    '>=': TokenType.GREATER_EQUAL, '[': TokenType.LEFT_BRACKET,
    '(.': TokenType.LEFT_BRACKET, '<': TokenType.LESS,
    '<=': TokenType.LESS_EQUAL, '(': TokenType.LEFT_PAREN,
    '-': TokenType.MINUS, '*': TokenType.MULTIPLY,
    '<>': TokenType.NOTEQUAL, '.': TokenType.PERIOD,
    '+': TokenType.PLUS, '^': TokenType.POINTER,
    '@': TokenType.POINTER, ']': TokenType.RIGHT_BRACKET,
    '.)': TokenType.RIGHT_BRACKET, ')': TokenType.RIGHT_PAREN,
    ';': TokenType.SEMICOLON, '..': TokenType.SUBRANGE
}


class Token:
    def __init__(self, token_type, location, value):
        assert isinstance(value, str), "Token values must be strings."
        assert location is None or isinstance(location, FileLocation), "Token locations must be FileLocations"
        self.token_type = token_type
        self.location = location
        self.value = value

    # Use a property for token_type so we can enforce that it is always a valid TokenType
    @property
    def token_type(self):
        return self.__token_type

    @token_type.setter
    def token_type(self, token_type):
        if isinstance(token_type, TokenType):
            self.__token_type = token_type
        else:  # pragma: no cover
            raise TypeError("Invalid Token Type")

    def __str__(self):  # pragma: no cover
        return 'type:{0:<18} value: {1:<15} loc: {2:<35}'.format(self.token_type, self.value, str(self.location))


class TokenStream:
    def __init__(self):
        self.token_list = []
        self.position = 0
        # TODO - see if we can do something with slices here.
        self.start_print_position = []
        self.end_print_position = []

    def set_start_print_position(self):
        self.start_print_position.append(self.position)

    def set_end_print_position(self):
        self.end_print_position.append(self.position)

    def print_start_to_end(self):
        # TODO - there is a more pythonic way of doing this I am certain
        return_str = ""
        start = self.start_print_position[-1]
        end = self.end_print_position[-1]

        i = start
        while i < end:
            if self.token_list[i].token_type == TokenType.CHARSTRING:
                return_str += "'" + self.token_list[i].value + "'"
            else:
                return_str += self.token_list[i].value
            return_str += " "
            i += 1
        del self.start_print_position[-1]
        del self.end_print_position[-1]
        return return_str

    def add_token(self, token):
        assert isinstance(token, Token), "Only Tokens may be added to TokenStream"
        self.token_list.append(token)

    # One can iterate over a TokenStream if desired, primarily for debugging purposes
    # (e.g. printing out all the tokens in the stream)
    def __iter__(self):  # pragma: no cover
        self.position = 0
        return self

    def __next__(self):  # pragma: no cover
        try:
            ret = self.token_list[self.position]
            self.position += 1
        except IndexError:
            raise StopIteration
        return ret

    def reset_position(self):
        self.position = 0

    def eat_token(self):
        from compiler_error import compiler_error_str
        try:
            ret = self.token_list[self.position]
        except IndexError:
            if self.position > 0:
                raise LexerException(
                    compiler_error_str("Missing 'end' statement or Unexpected end of file",
                                       self.token_list[self.position - 1]))
            else:
                raise LexerException(compiler_error_str("Cannot compile empty file"))
        self.position += 1
        return ret

    def peek_previous_token(self):
        if self.position > 0:
            return self.token_list[self.position - 1]
        else:  # pragma: no cover
            return None

    def peek_token(self):
        from compiler_error import compiler_error_str
        try:
            return_token = self.token_list[self.position]
        except IndexError:
            if self.position > 0:
                raise LexerException(
                    compiler_error_str("Missing 'end' statement or Unexpected end of file",
                                       self.token_list[self.position - 1]))
            else:
                raise LexerException(compiler_error_str("Cannot compile empty file"))
        assert isinstance(return_token, Token), "TokenStream.peek_token: Non-token found in stream"
        return return_token

    def peek_token_type(self):
        # returns the type of the next token in the token list, but does not advance the position.  Used
        # when interpretation of a token varies based on the token that follows.
        # returns None if we are past the end of the token list.
        try:
            return_token = self.token_list[self.position].token_type
        except IndexError:
            return_token = None
        return return_token

    def peek_multi_token_type(self, num):
        # returns a list of the types of the next num tokens in the token list, but does not advance the position.
        # Used when interpretation of a token varies based on multiple tokens that follow.  Returns the empty
        # list if we are past the end of the token list.  If we are not past the end of the token list, but there
        # are fewer than num tokens left in the list, then will return all remaining tokens in the token list.

        return_list_of_token_types = []
        i = self.position
        try:
            while i < self.position + num:
                return_list_of_token_types.append(self.token_list[i].token_type)
                i += 1
        except IndexError:  # pragma: no cover
            pass
        return return_list_of_token_types


class Lexer:
    def __init__(self, filename):
        self.tokenstream = TokenStream()
        self.text = ""
        self.length = 0
        self.current_position = 0
        self.location = FileLocation(filename, 1, 1, "")

    def at_eof(self):
        return self.current_position >= self.length

    def peek(self):
        # returns the next character in the input text, or "" if we are past the end of the input.
        if self.at_eof():
            return ""
        else:
            return self.text[self.current_position]

    def peek_ahead(self, num):
        # returns the character that is num characters ahead.  Passing 0 for num is synonymous with peek().
        assert (num >= 0), "Cannot peek behind current position"
        pos = self.current_position + num
        if pos < self.length:
            return self.text[pos]
        else:  # pragma: no cover
            return ""

    def peek_rest_of_current_line(self):
        # returns the text from the current position until the end of current line or end of file, whichever
        # comes first.
        i = 0
        while not self.at_eof() and self.text[self.current_position + i] != "\n":
            i += 1
        if i == 0:
            return ""
        else:
            return self.peek_multi(i)

    def peek_multi(self, num):
        return self.text[self.current_position:self.current_position + num]

    def eat(self):
        if self.at_eof():  # pragma: no cover
            raise IndexError("Length Exceeded")
        else:
            return_str = self.text[self.current_position]
            self.current_position += 1
            if return_str == '\n':
                self.location.line += 1
                self.location.column = 1
                self.location.current_line_str = self.peek_rest_of_current_line()
            elif return_str == '\t':
                self.location.column += NUM_SPACES_IN_TAB
            else:
                self.location.column += 1
            return return_str

    def eat_multi(self, num):
        return_str = ""
        for i in range(num):
            return_str += self.eat()
        return return_str

    def eat_whitespace(self):
        while self.peek().isspace():
            self.eat()

    def eat_identifier(self):
        # Definition of identifier in section 6.1.3 of ISO Standard is letter { letter | digit } .
        # This function validates that the next character in the input string is a letter, and if so,
        # returns the identifier.  Returns empty string if the next character in the input stream
        # is not alphabetic.
        return_str = ""
        if self.peek().isalpha():
            return_str = self.eat()
            while self.peek().isalnum():
                return_str += self.eat()
        return return_str

    def eat_comment(self):
        # Definition of commentary in section 6.1.8 of the ISO standard is
        # ( '{' | '(*' ) commentary ( '}' | '*)' ).  The actual commentary itself can be any arbitrary string of
        # characters, on multiple lines.  Comments do not nest, so the string "{ (* a comment *) }" is invalid, as the
        # comment ends on the "*)," so the "}" would be flagged as an invalid token.
        # Returns empty string if the next character(s) in the input stream is not a comment opening.
        assert self.peek() == '{' or self.peek_multi(2) == '(*'

        return_str = ""
        if self.peek() == '{':
            self.eat()
        elif self.peek_multi(2) == '(*':
            self.eat_multi(2)

        while self.peek() != '}' and self.peek_multi(2) != '*)':
            return_str += self.eat()
        if self.peek() == '}':
            self.eat()
        else:  # eat the "*)"
            self.eat_multi(2)
        return return_str

    def eat_real_number(self):
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
        # As a note, the 'e' in the unsigned-real can be lowercase or uppercase.
        #
        # Returns empty string if the next character in the input stream is not numeric.
        from compiler_error import compiler_error_str
        return_str = ""
        while self.peek().isnumeric():
            return_str += self.eat()
            if self.peek() == '.':
                if self.peek_ahead(1).isnumeric():
                    return_str += self.eat()  # grab the period
                    while self.peek().isnumeric():
                        return_str += self.eat()
                else:
                    # Cannot end a real with a period and no digits following.
                    error_str = compiler_error_str("Invalid character '.'", None, self.location)
                    raise ValueError(error_str)
            if self.peek().lower() == 'e':
                if self.peek_ahead(1) in ['+', '-'] and self.peek_ahead(2).isnumeric():
                    return_str += self.eat_multi(2)  # grab the 'e' and the sign
                    while self.peek().isnumeric():
                        return_str += self.eat()
                elif self.peek_ahead(1).isnumeric():
                    return_str += self.eat()  # grab the 'e'
                    while self.peek().isnumeric():
                        return_str += self.eat()
                else:
                    error_str = compiler_error_str(
                        "Invalid real number format: {}{}{}".format(return_str, self.peek(), self.peek_ahead(1)), None,
                        self.location)
                    raise ValueError(error_str)
        return return_str

    def eat_character_string(self):
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

        return_str = ''
        if self.peek() == "'":
            self.eat()  # remove the apostrophe
            done = False
            while not done:
                if self.peek_multi(2) == "''":
                    return_str += "'"  # add the single apostrophe
                    self.eat_multi(2)  # eat both apostrophes
                elif self.peek() == "'":
                    self.eat()  # eat the closing apostrophe
                    done = True
                else:
                    try:
                        return_str += self.eat()
                    except IndexError:
                        raise LexerException("Unterminated character string")
        return return_str

    def lex(self):
        from compiler_error import compiler_error_str

        assert self.location.filename != "", "Filename not set, cannot Tokenize"
        try:
            f = open(self.location.filename, "r")
            self.text = f.read()
            self.length = len(self.text)
            f.close()
            self.location.current_line_str = self.peek_rest_of_current_line()
        except FileNotFoundError:
            raise LexerException("Invalid filename: {}".format(self.location.filename))

        self.eat_whitespace()
        while not self.at_eof():
            # Remember where this next token starts, since that is the position a user would want to see in an error
            # It needs to be a copy, else every token we create in every iteration would share the same location
            # object.
            current_location = copy(self.location)
            try:
                if self.peek() == "'":
                    val = self.eat_character_string()
                    self.tokenstream.add_token(Token(TokenType.CHARSTRING, current_location, val))
                elif self.peek().isalpha():
                    val = self.eat_identifier()
                    if val.lower() in TOKEN_TYPE_LOOKUP.keys():
                        token_type = TOKEN_TYPE_LOOKUP[val.lower()]
                    else:
                        token_type = TokenType.IDENTIFIER
                    self.tokenstream.add_token(Token(token_type, current_location, val))
                elif self.peek().isnumeric():
                    # could be a real or an integer.  Read until the next non-numeric character.  If that character
                    # is an e, E, or a . followed by a digit then it is a real, else it is an integer.
                    lookahead = 1
                    while self.peek_ahead(lookahead).isnumeric():
                        lookahead += 1
                    if ((self.peek_ahead(lookahead) == '.' and self.peek_ahead(lookahead + 1).isnumeric()) or
                            self.peek_ahead(lookahead).lower() == 'e'):
                        val = self.eat_real_number()
                        self.tokenstream.add_token(Token(TokenType.UNSIGNED_REAL, current_location, val))
                    elif (self.peek_ahead(lookahead) == '.' and self.peek_ahead(lookahead + 1) != '.' and
                          self.peek_ahead(lookahead + 1) != ')'):
                        # if we see two periods, it is a subrange token.  If we see a period followed by a paren,
                        # it's a lexical alternative for right bracket.  If we see one period otherwise, it is invalid;
                        # see definition of <unsigned-real>.  Without this special case, the error is
                        # 'Expected 'end' but saw '.' which is unhelpful.
                        error_str = compiler_error_str(
                            'Invalid real number format: "{}"'.format(self.peek_multi(lookahead + 1)), None,
                            current_location)
                        raise ValueError(error_str)
                    else:
                        val = ""
                        while self.peek().isnumeric():
                            val += self.eat()
                        self.tokenstream.add_token(Token(TokenType.UNSIGNED_INT, current_location, val))
                elif self.peek() == '{' or self.peek_multi(2) == '(*':
                    self.eat_comment()
                    # Comments are totally ignored from here forward, so we do not add those to the tokenstream.
                elif self.peek() in ['+', '-', '*', '/', '=', '<', '>', '[', ']', '.', ',', ':', ';',
                                     '^', '(', ')', '@']:
                    # Test first for the 2-character symbols, and if none of those match, we know
                    # we have a single-character symbol.
                    if self.peek_multi(2) in [':=', '>=', '<=', '<>', '(.', '.)', '..']:
                        val = self.eat_multi(2)
                    else:
                        val = self.eat()
                    token_type = SYMBOL_LOOKUP[val]
                    self.tokenstream.add_token(Token(token_type, current_location, val))
                else:
                    raise LexerException('Unexpected character: {}'.format(self.peek()))
            except Exception as e:
                if isinstance(e, ValueError):
                    raise e
                else:
                    raise LexerException(compiler_error_str(e, None, current_location))

            self.eat_whitespace()
