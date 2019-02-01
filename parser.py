from enum import Enum, unique, auto
from lexer import TokenType, Token, TokenStream


# Helper Function
def token_errstr(tok, msg="Invalid Token"):
    assert(isinstance(tok, Token))
    return msg + " {0} in {1}".format(tok.value, str(tok.location))


class ParseException(Exception):
    pass


@unique
class ASTAttributes(Enum):
    PROGRAM_NAME = auto()  # the identifier that names the program.  Not used in compilation.
    PROGRAM_INPUT = auto()  # was the program-parameter INPUT provided
    PROGRAM_OUTPUT = auto()  # was the program-parameter OUTPUT provided


class AST:
    def __init__(self, token, comment=None):
        assert(isinstance(token, Token))
        self.token = token
        self.comment = comment  # will get put on the line emitted in the assembly code if populated.
        self.children = []
        self.attrs = {}  # different types of tokens require different attributes

    def rpn_print(self, level=0):
        for x in self.children:
            x.rpn_rpint(level + 1)
        print((level * " ") + str(self.token))


class Parser:
    def __init__(self, tokenstream):
        assert(isinstance(tokenstream, TokenStream))
        self.tokenstream = tokenstream
        self.AST = None

    def getexpectedtoken(self, tokentype):
        assert(isinstance(tokentype, TokenType))
        ret = self.tokenstream.eattoken()
        if ret.tokentype != tokentype:
            errstr = "Expected {0}, saw {1} in {2}".format(str(tokentype), str(ret.tokentype), str(ret.location))
            raise ParseException(errstr)
        return ret

    def parse_program(self):
        # 6.10 of the ISO Standard defines the program statement.  However, other than the program parameters
        # "input" and "output" the use of program parameters is implementation-defined.  Our implementation elects
        # not to use program parameters other than "input" and "output."  So, instead of having program parameter
        # list map directly to identifier-list, we are going to map it to a specific set of strings.
        # <program> ::= <program-heading> ";" <program-block> "."
        # <program-heading> ::= <program> <identifier> [ "(" <program-parameter-list> ")" ]
        # <program-parameter-list ::= <program-parameter> ["," <program-parameter>]
        # <program-parameter> ::= "input" | "output"

        ret = AST(self.getexpectedtoken(TokenType.PROGRAM))
        tok = self.getexpectedtoken(TokenType.IDENTIFIER)
        ret.attrs[ASTAttributes.PROGRAM_NAME] = tok.value
        if self.tokenstream.peektokentype() == TokenType.LPAREN:
            self.getexpectedtoken(TokenType.LPAREN)
            while self.tokenstream.peektokentype() != TokenType.RPAREN:
                tok = self.tokenstream.eattoken()
                if tok.tokentype == TokenType.INPUT:
                    if ASTAttributes.PROGRAM_INPUT not in ret.attrs.keys():
                        ret.attrs[ASTAttributes.PROGRAM_INPUT] = True
                        if self.tokenstream.peektokentype() != TokenType.RPAREN:
                            self.getexpectedtoken(TokenType.COMMA)
                    else:
                        raise ParseException(token_errstr(tok, "Duplicate program parameter"))
                elif tok.tokentype == TokenType.OUTPUT:
                    if ASTAttributes.PROGRAM_OUTPUT not in ret.attrs.keys():
                        ret.attrs[ASTAttributes.PROGRAM_OUTPUT] = True
                        if self.tokenstream.peektokentype() != TokenType.RPAREN:
                            self.getexpectedtoken(TokenType.COMMA)
                    else:
                        raise ParseException(token_errstr(tok, "Duplicate program parameter"))
                else:
                    raise ParseException(token_errstr(tok, "Invalid program parameter"))
            self.getexpectedtoken(TokenType.RPAREN)
        self.getexpectedtoken(TokenType.SEMICOLON)
        return ret

    def parse(self):
        self.tokenstream.resetpos()
        self.AST = self.parse_program()
