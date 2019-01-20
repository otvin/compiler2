from enum import Enum, unique

''' named tokenize so that we do not conflict with the package Lib/token '''


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
    CHAR = 'char'
    # String Type is defined TODO: Where
    STRING = 'string'

    # Most of the required procedures in 6.6.5 of the ISO standard are going to need to be handled by the compiler.
    # File Handling Procedures are defined in 6.6.5.2
    REWRITE = "rewrite"
    PUT = "put"
    RESET = "reset"
    GET = "get"
    # Read() and Write() can be defined in terms of Get() and Put().  However, since these functions
    # are variadic (they can have variable-length parameter lists) and are the only Pascal functions
    # with this property, handling them in the compiler will be easier.
    READ = "read"
    WRITE = "write"
    # readln() is defined in 6.9.2
    READLN = "readln"
    # writeln() is defined in 6.9.4
    WRITELN = 'writeln'

    # Dynamic Allocation Procedures are defined in 6.6.5.3 of the ISO Standard
    NEW = "new"
    DISPOSE = "dispose"

    # Transfer Procedures are defined in 6.6.5.4 of the ISO Standard
    PACK = "pack"
    UNPACK = "unpack"

    # For the required functions in 6.6.6 of the ISO Standard, some could be handled outside the compiler, but
    # for now, we will handle them in the compiler.  As a note, this will prevent overriding the definitions,
    # compared to writing these in Pascal in a Unit that could be optionally included.
    # Arithmetic Functions are defined in 6.6.6.2
    ABS = "abs"
    SQR = "sqr"
    SIN = "sin"
    COS = "cos"
    EXP = "exp"
    LN = "ln"
    SQRT = "sqrt"
    ARCTAN = "arctan"

    # Transfer Functions are defined in 6.6.6.3 of the ISO Standard
    TRUNC = "trunc"
    ROUND = "round"

    # Ordinal Functions are defined in 6.6.6.4 of the ISO Standard
    ORD = "ord"
    CHR = "chr"
    SUCC = "succ"
    PRED = "pred"

    # Boolean Functions are defined in 6.6.6.5 of the ISO Standard
    ODD = "odd"
    EOF = "eof"
    EOLN = "eoln"

    # Required Constant is defined in 6.7.2.2 of the ISO Standard
    MAXINT = "maxint"

    def __str__(self):
        return self.value


class Token:
    def __init__(self, tokentype, line, column, filename):
        self.tokentype = tokentype
        self.line = line
        self.column = column
        self.filename = filename

    # Make the tokentype a property TO-DO finish comment
    @property
    def tokentype(self):
        return self.__tokentype

    @tokentype.setter
    def tokentype(self, t):
        if isinstance(t, TokenType):
            self.__tokentype = t
        else:  # pragma: no cover
            raise ValueError("Invalid Token Type")
