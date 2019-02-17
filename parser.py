from enum import Enum, unique, auto
from lexer import TokenType, Token, TokenStream, LexerException
from symboltable import StringLiteral, LiteralTable, SymbolTable


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


# TODO - should an AST be a container with AST Nodes inside?
class AST:
    def __init__(self, token, parent, comment=None):
        assert(isinstance(token, Token))
        self.token = token
        self.comment = comment  # will get put on the line emitted in the assembly code if populated.
        self.children = []
        if parent is not None:
            assert(isinstance(parent, AST))
        self.parent = parent  # pointer back to the parent node in the AST
        self.symboltable = None  # will only be defined for Procedure, Function, and Program tokens
        self.attrs = {}  # different types of tokens require different attributes

    def rpn_print(self, level=0):
        for x in self.children:
            x.rpn_print(level + 1)
        print((level * " ") + str(self.token))

    def nearest_symboltable(self):
        ptr = self
        while ptr.symboltable is not None:
            ptr = ptr.parent
            # the root of the AST has a symboltable for globals, so ptr should never get to None
            assert ptr is not None
        return ptr.symboltable


# TODO - add a class for a parsewarning/parseerror - likely the same thing, a string, a location, maybe a level?
class Parser:
    def __init__(self, tokenstream):
        assert(isinstance(tokenstream, TokenStream))
        self.tokenstream = tokenstream
        self.AST = None
        self.parseerrorlist = []
        self.parsewarninglist = []
        self.literaltable = LiteralTable()

    def getexpectedtoken(self, tokentype):
        assert(isinstance(tokentype, TokenType))
        ret = self.tokenstream.eattoken()
        if ret.tokentype != tokentype:
            errstr = "Expected {0} but saw '{1}' in {2}".format(str(tokentype), str(ret.value), str(ret.location))
            raise ParseException(errstr)
        return ret

    def parse_labeldeclarationpart(self, parent_ast):
        return None

    def parse_constantdefinitionpart(self, parent_ast):
        return None

    def parse_typedefinitionpart(self, parent_ast):
        return None

    def parse_variabledeclarationpart(self, parent_ast):
        return None

    def parse_procedureandfunctiondeclarationpart(self, parent_ast):
        return None

    def parse_statement(self, parent_ast):
        # for now, we are only going to parse the WRITE() statement and an integer or string literal.
        ret = AST(self.getexpectedtoken(TokenType.WRITE), parent_ast)
        self.getexpectedtoken(TokenType.LPAREN)
        # TODO: When we support other Output types, we need to actually parse the first parameter
        # to see if it is a file-variable.
        # TODO: The file-variable, or implied file-variable OUTPUT should be a symbol.
        if self.tokenstream.peektokentype() == TokenType.OUTPUT:
            ret.children.append(AST(self.getexpectedtoken(TokenType.OUTPUT), parent_ast))
            self.getexpectedtoken(TokenType.COMMA)
        isneg = False
        if self.tokenstream.peektokentype() == TokenType.CHARSTRING:
            # LiteralTable.add() allows adding duplicates
            charstrtok = self.getexpectedtoken(TokenType.CHARSTRING)
            assert isinstance(charstrtok, Token)
            self.literaltable.add(StringLiteral(charstrtok.value, charstrtok.location))
            ret.children.append(AST(charstrtok, ret))
        else:
            if self.tokenstream.peektokentype() == TokenType.MINUS:
                # TODO - this won't work in general because ---3 is still legal, but this only accepts one minus
                # will get fixed when we do factors/expressions
                minus = self.getexpectedtoken(TokenType.MINUS)
                isneg = True
                uinttok = self.getexpectedtoken(TokenType.UNSIGNED_INT)
                numtok = Token(TokenType.SIGNED_INT, minus.location, "-" + uinttok.value)
            else:
                numtok = self.getexpectedtoken(TokenType.UNSIGNED_INT)
            child = AST(numtok, ret)
            numval = int(numtok.value)
            if isneg:
                numval *= -1  # this may be a bug
            ret.children.append(child)
        self.getexpectedtoken(TokenType.RPAREN)
        return ret

    def parse_statementpart(self, parent_ast):
        # 6.2.1 defines statement-part simply as <statement-part> ::= <compound-statement>
        # 6.8.3.2 defines <compound-statement> ::= "begin" <statement-sequence> "end"
        # 6.8.3.1 defines <statement-sequence> ::= <statement> [ ";" <statement> ]
        # The <statement-part> is the only portion of the <block> that is required.  Each of the
        # other parts, i.e. label declaration, constant definition, type definition, variable declaration
        # and procedure/function declaration are optional.
        #
        # This function returns an AST node using the BEGIN as the token, and with one child for each
        # statement.
        ret = AST(self.getexpectedtoken(TokenType.BEGIN), parent_ast)
        ret.children.append(self.parse_statement(parent_ast))
        while self.tokenstream.peektokentype() == TokenType.SEMICOLON:
            self.getexpectedtoken(TokenType.SEMICOLON)
            if self.tokenstream.peektokentype() != TokenType.END:
                ret.children.append(self.parse_statement(parent_ast))
        # The expected token here is an END.  However, if the END does not appear, we will try to keep parsing
        # so that other parse errors could be displayed later.  It is frustrating for an end user to have
        # compilation die on the first error.
        endtok = self.tokenstream.eattoken()
        if endtok.tokentype != TokenType.END:
            errstr = "Expected 'end' but saw '{0}' in {1}".format(str(endtok.value), str(endtok.location))
            self.parseerrorlist.append(errstr)
            while endtok.tokentype != TokenType.END:
                try:
                    endtok = self.tokenstream.eattoken()
                except LexerException as le:
                    self.parseerrorlist.append(str(le))
                    return ret
        return ret

    def parse_block(self, parent_ast):
        # 6.2.1 of the ISO standard defines a block.  The BNF:
        # <block> ::= <label-declaration-part> <constant-definition-part> <type-definition-part>
        #             <variable-declaration-part> <procedure-and-function-declaration-part>
        #             <statement-part>
        # Unlike the rest of the parse_* functions, this one returns a list of AST nodes to become the
        # children of the AST being returned by the calling function.

        ret = []
        a = self.parse_labeldeclarationpart(parent_ast)
        if a is not None:
            ret.append(a)
        a = self.parse_constantdefinitionpart(parent_ast)
        if a is not None:
            ret.append(a)
        a = self.parse_typedefinitionpart(parent_ast)
        if a is not None:
            ret.append(a)
        a = self.parse_variabledeclarationpart(parent_ast)
        if a is not None:
            ret.append(a)
        a = self.parse_procedureandfunctiondeclarationpart(parent_ast)
        if a is not None:
            ret.append(a)
        # Only the <statement-part> is required; other parts above are optional
        a = self.parse_statementpart(parent_ast)
        ret.append(a)
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
        # <program-block> ::= <block>

        ret = AST(self.getexpectedtoken(TokenType.PROGRAM), None)
        # this will be the symbol table for globals
        ret.symboltable = SymbolTable()
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
        ret.children = self.parse_block(ret)
        self.getexpectedtoken(TokenType.PERIOD)
        return ret

    def parse(self):
        self.tokenstream.resetpos()
        self.AST = self.parse_program()
        if len(self.parseerrorlist) > 0:
            for e in self.parseerrorlist:
                print(e)
            raise ParseException("Parsing Failed")
