from enum import Enum, unique, auto
from lexer import TokenType, Token, TokenStream, LexerException
from symboltable import StringLiteral, NumericLiteral, LiteralTable, SymbolTable, VariableSymbol, ParameterList, \
    ActivationSymbol, FunctionResultVariableSymbol, Parameter, SymbolException, ConstantSymbol
import pascaltypes

'''
BNF syntax notes - as defined in Section 3 of the ISO standard, modified by me to 
resemble more common BNF terminology.

::=         - shall be defined to  be
[ x ]       - x is optional; there shall be exactly 0 or 1 instances of x.
{ x }       - there shall be 0 or more instances of x
|           - alternatively
( x | y)    - either of x or y
"xyz"       - the terminal symbol xyz
<xyz>       - the non-terminal symbol xyz, which shall be defined elsewhere in the BNF
'''


# Helper Functions
def token_errstr(tok, msg="Invalid Token:"):
    assert isinstance(tok, Token), "Non-token generating token error {}".format(msg)
    return msg + " '{0}' in {1}".format(tok.value, str(tok.location))


def isrelationaloperator(tokentype):
    # 6.7.2.1 <relational-operator> ::= "=" | "<>" | "<" | ">" | "<=" | ">=" | "in"
    assert isinstance(tokentype, TokenType)
    if tokentype in (TokenType.EQUALS, TokenType.NOTEQUAL, TokenType.LESS, TokenType.GREATER,
                     TokenType.LESSEQ, TokenType.GREATEREQ, TokenType.IN):
        return True
    else:
        return False


def ismultiplyingoperator(tokentype):
    # 6.7.2.1 <multiplying-operator> ::= "*" | "/" | "div" | "mod" | "and"
    assert isinstance(tokentype, TokenType)
    if tokentype in (TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.IDIV, TokenType.MOD, TokenType.AND):
        return True
    else:
        return False


def isaddingoperator(tokentype):
    # 6.7.2.1 <adding-operator> ::= "+" | "-" | "or"
    assert isinstance(tokentype, TokenType)
    if tokentype in (TokenType.PLUS, TokenType.MINUS, TokenType.OR):
        return True
    else:
        return False


def is_isorequiredfunction(tokentype):
    # 6.6.6 in the ISO Standard lists required functions.
    assert isinstance(tokentype, TokenType)
    if tokentype in (TokenType.ABS, TokenType.SQR, TokenType.SIN, TokenType.COS, TokenType.EXP,
                     TokenType.LN, TokenType.SQRT, TokenType.ARCTAN, TokenType.TRUNC,
                     TokenType.ROUND, TokenType.ORD, TokenType.CHR, TokenType.SUCC, TokenType.PRED,
                     TokenType.ODD, TokenType.EOF, TokenType.EOLN):
        return True
    else:
        return False


def startsstructuredstatement(tokentype):
    # 6.8.3.1 - <structured-statement> ::= <compound-statement> | <conditional-statement>
    #                                       | <repetitive-statement> | <with-statement>

    # compound statement starts with "begin"
    # conditional statements start with "if" or "case"
    # repetitive statements start with "repeat," "while,"or "for"
    # with statements start with "with"

    if tokentype in (TokenType.BEGIN, TokenType.IF, TokenType.CASE, TokenType.REPEAT, TokenType.WHILE,
                     TokenType.FOR, TokenType.WITH):
        return True
    else:
        return False


class ParseException(Exception):
    pass


@unique
class ASTAttributes(Enum):
    PROGRAM_NAME = auto()  # the identifier that names the program.  Not used in compilation.
    PROGRAM_INPUT = auto()  # was the program-parameter INPUT provided
    PROGRAM_OUTPUT = auto()  # was the program-parameter OUTPUT provided


# TODO - should an AST be a container with AST Nodes inside?
class AST:
    def __init__(self, token, parent, comment=""):
        assert(isinstance(token, Token)), "AST.__init__: AST requires a token"
        self.token = token
        self.comment = comment  # will get put on the line emitted in the assembly code if populated.
        self.children = []
        if parent is not None:
            assert(isinstance(parent, AST)), "AST.__init__:Parent of AST must be an AST"
        self.parent = parent  # pointer back to the parent node in the AST
        self.symboltable = None  # will only be defined for Procedure, Function, and Program tokens
        self.paramlist = None  # will only be defined for Procedure and Function tokens
        # TODO - is self.attrs really needed, or is it just for the three Program-level attributes?
        self.attrs = {}  # different types of tokens require different attributes

    def initsymboltable(self):
        self.symboltable = SymbolTable()
        # only go forward if not the root of the AST, else leave the parent of the SymbolTable as None
        if self.parent is not None:
            ptr = self.parent
            while ptr.symboltable is None:
                ptr = ptr.parent
                # the root of the AST has a symboltable for globals, so since this node is not the root
                # it should never get to None.
                assert ptr is not None, "AST.nearest_symboltable: No symboltable in AST ancestry"
            assert isinstance(ptr.symboltable, SymbolTable)
            self.symboltable.parent = ptr.symboltable

    def initparamlist(self):
        self.paramlist = ParameterList()

    def rpn_print(self, level=0):  # pragma: no cover
        # used only for debugging
        for x in self.children:
            x.rpn_print(level + 1)
        if self.comment == "":
            ret = "{}{}".format((level * " "), str(self.token))
        else:
            ret = "{}{}\t\t;{}".format((level * " "), str(self.token), self.comment)
        print(ret)

    def nearest_symboltable(self):
        ptr = self
        while ptr.symboltable is None:
            ptr = ptr.parent
            # the root of the AST has a symboltable for globals, so ptr should never get to None
            assert ptr is not None, "AST.nearest_symboltable: No symboltable in AST ancestry"
        assert isinstance(ptr.symboltable, SymbolTable)
        return ptr.symboltable

    def dump_symboltables(self):  # pragma: no cover
        # used only for debugging
        for child in self.children:
            child.dump_symboltables()
        if self.symboltable is not None:
            print(str(self.symboltable))
            print("*****")


# TODO - add a class for a parsewarning/parseerror - likely the same thing, a string, a location, maybe a level?
class Parser:
    def __init__(self, tokenstream):
        assert(isinstance(tokenstream, TokenStream)), "Parser.__init__: Can only parse TokenStreams"
        self.tokenstream = tokenstream
        self.AST = None
        self.parseerrorlist = []
        self.parsewarninglist = []
        self.literaltable = LiteralTable()

    def getexpectedtoken(self, tokentype):
        assert(isinstance(tokentype, TokenType)), "Parser.getexpectedtoken: Expected Token must be a token"
        ret = self.tokenstream.eattoken()
        if ret.tokentype != tokentype:
            if tokentype == tokentype.SEMICOLON:
                # TODO - insert a semicolon into the stream and allow parsing to continue
                errstr = "Semicolon expected in {}".format(str(ret.location))
            else:
                errstr = "Expected '{0}' but saw '{1}' in {2}".format(str(tokentype), str(ret.value), str(ret.location))
            raise ParseException(errstr)
        assert isinstance(ret, Token)
        return ret

    def parse_labeldeclarationpart(self, parent_ast):
        return None

    def parse_constantdefinitionpart(self, parent_ast):
        # 6.2.1 <constant-definition-part> ::= [ "const" <constant-definition> ";" {<constant-definition> ";"} ]
        # 6.3 <constant-definition> ::= <identifier> "=" <constant>
        # 6.3 <constant> ::= [sign] (<unsigned-number> | <constant-identifier>) | <character-string>
        # 6.1.5 <sign> ::= "+" | "-"
        # 6.3 <constant-identifier> ::= <identifier>
        # 6.1.7 <character-string> ::= "'" <string-element> {<string-element>} "'"

        # Note - this appears to state that you cannot have a constant of a user-defined type, but you can
        # do:
        #   const pi = 3.14; negpi = -pi;
        # <constant-identifier> can be an identifier of another constant, or one of the required constants
        #   maxint, true, or false.

        if self.tokenstream.peektokentype() == TokenType.CONST:
            assert isinstance(parent_ast.symboltable, SymbolTable), \
                "Parser.parse_constantdefinitionpart: missing symboltable"
            self.getexpectedtoken(TokenType.CONST)
            done = False
            while not done:
                # p.65 of [Cooper] states that if a constant has a sign then the next token must be
                # a real, an integer, or a real/integer constant.  That can't be captured in the BNF.

                const_id = self.getexpectedtoken(TokenType.IDENTIFIER)
                self.getexpectedtoken(TokenType.EQUALS)
                if self.tokenstream.peektokentype() == TokenType.MINUS:
                    self.getexpectedtoken(TokenType.MINUS)
                    isneg = True
                    sawsign = True
                else:
                    if self.tokenstream.peektokentype() == TokenType.PLUS:
                        sawsign = True
                        self.getexpectedtoken(TokenType.PLUS)
                    else:
                        sawsign = False
                    isneg = False



                if self.tokenstream.peektokentype() == TokenType.UNSIGNED_REAL:
                    realtok = self.getexpectedtoken(TokenType.UNSIGNED_REAL)
                    if isneg:
                        tokval = "-" + realtok.value
                    else:
                        tokval = realtok.value
                    self.literaltable.add(NumericLiteral(tokval, realtok.location, pascaltypes.RealType()))
                    parent_ast.symboltable.add(ConstantSymbol(const_id.value, const_id.location,
                                                              pascaltypes.RealType(), tokval))
                elif self.tokenstream.peektokentype() == TokenType.UNSIGNED_INT:
                    inttok = self.getexpectedtoken(TokenType.UNSIGNED_INT)
                    if isneg:
                        tokval = "-" + inttok.value
                    else:
                        tokval = inttok.value
                    parent_ast.symboltable.add(ConstantSymbol(const_id.value, const_id.location,
                                                              pascaltypes.IntegerType(), tokval))
                elif self.tokenstream.peektokentype() == TokenType.MAXINT:
                    self.getexpectedtoken(TokenType.MAXINT)
                    if isneg:
                        tokval = pascaltypes.STRNEGMAXINT
                    else:
                        tokval = pascaltypes.STRMAXINT
                    parent_ast.symboltable.add(ConstantSymbol(const_id.value, const_id.location,
                                                              pascaltypes.IntegerType(), tokval))
                elif self.tokenstream.peektokentype() in (TokenType.TRUE, TokenType.FALSE):
                    if sawsign:
                        errstr = "Cannot have a sign before a Boolean constant in {}".format(const_id.location)
                        raise ParseException(errstr)
                    booltok = self.tokenstream.eattoken()
                    parent_ast.symboltable.add(ConstantSymbol(const_id.value, const_id.location,
                                                              pascaltypes.BooleanType(), booltok.value))
                elif self.tokenstream.peektokentype() == TokenType.CHARSTRING:
                    if sawsign:
                        errstr = "Cannot have a sign before a string constant in {}".format(const_id.location)
                        raise ParseException(errstr)
                    charstrtok = self.getexpectedtoken(TokenType.CHARSTRING)
                    self.literaltable.add(StringLiteral(charstrtok.value, charstrtok.location))
                    parent_ast.symboltable.add(ConstantSymbol(const_id.value, const_id.location,
                                                              pascaltypes.StringLiteralType(), charstrtok.value))
                elif self.tokenstream.peektokentype() == TokenType.IDENTIFIER:
                    ident_token = self.getexpectedtoken(TokenType.IDENTIFIER)
                    if not parent_ast.symboltable.existsanywhere(ident_token.value):
                        if ident_token.value == const_id.value:
                            errstr = "Self-referencing constant definition '{}' in {}"
                            errstr = errstr.format(ident_token.value, ident_token.location)
                        else:
                            errstr = "Undefined Identifier: '{}' in {}".format(ident_token.value, ident_token.location)
                        raise ParseException(errstr)
                    sym = parent_ast.symboltable.fetch(ident_token.value)
                    if not isinstance(sym, ConstantSymbol):
                        errstr = "Constant '{}' must be defined as a literal or another constant, cannot use '{}' in {}"
                        errstr = errstr.format(const_id.value, ident_token.value, ident_token.location)
                        raise ParseException(errstr)
                    if sawsign:
                        if isinstance(sym.pascaltype, pascaltypes.RealType) or \
                                isinstance(sym.pascaltype, pascaltypes.IntegerType):
                            if isneg:
                                if sym.value[0] == "-":
                                    tokval = sym.value[1:]  # remove the negative
                                else:
                                    tokval = "-" + sym.value
                                # If we define a constant as negative another constant, we need to ensure the
                                # literal value is in the literals table if it's a real constant.
                                # LiteralTable.add() allows adding duplicates and filters them out.
                                if isinstance(sym.pascaltype, pascaltypes.RealType):
                                    self.literaltable.add(NumericLiteral(tokval, ident_token.location,
                                                                         pascaltypes.RealType()))
                            else:
                                tokval = sym.value
                        else:
                            errstr = "Constant '{}' is not numeric."
                            errstr += " Cannot define constant '{}' by putting a sign before a non-numeric constant."
                            errstr += " In: {}"
                            errstr = errstr.format(ident_token.value, const_id.value, ident_token.location)
                            raise ParseException(errstr)
                    else:
                        tokval = sym.value

                    parent_ast.symboltable.add(ConstantSymbol(const_id.value, const_id.location,
                                                              sym.pascaltype, tokval))
                else:
                    nexttok = self.tokenstream.eattoken()
                    errstr = "Unexpected token {} in {}.".format(str(nexttok.value), nexttok.location)
                    raise ParseException(errstr)

                self.getexpectedtoken(TokenType.SEMICOLON)
                if self.tokenstream.peektokentype() != TokenType.IDENTIFIER:
                    done = True

        return None

    def parse_typedefinitionpart(self, parent_ast):
        return None

    def parse_typeidentifier(self):
        # Types can be very flexibile due to user-defined types, which we do not support now.  For now, we will use
        # <type-identifier> ::= "integer" | "real" | "boolean"
        #
        # This function returns the type itself.

        type_token = self.tokenstream.eattoken()
        if type_token.tokentype == TokenType.INTEGER:
            symboltype = pascaltypes.IntegerType()
        elif type_token.tokentype == TokenType.REAL:
            symboltype = pascaltypes.RealType()
        elif type_token.tokentype == TokenType.BOOLEAN:
            symboltype = pascaltypes.BooleanType()
        else:
            raise ParseException("Invalid type denoter: {}".format(str(type_token)))
        return symboltype

    def parse_identifierlist(self):
        # 6.4.2.3 <identifier-list> ::= <identifier> { "," <identifier> }
        # 6.1.3 <identifier> ::= <letter> {<letter> | <digit>}
        #
        # returns a python list of one or more identifier tokens
        ret = [self.getexpectedtoken(TokenType.IDENTIFIER)]
        while self.tokenstream.peektokentype() == TokenType.COMMA:
            self.getexpectedtoken(TokenType.COMMA)
            ret.append(self.getexpectedtoken(TokenType.IDENTIFIER))
        return ret

    def parse_variabledeclarationpart(self, parent_ast):
        # 6.2.1 <variable-declaration-part> ::= [ "var" <variable-declaration> ";" {<variable-declaration> ";"} ]
        # 6.5.1 <variable-declaration> ::= <identifier-list> ":" <type-denoter>
        # 6.4.2.3 <identifier-list> ::= <identifier> { "," <identifier> }
        # 6.1.3 <identifier> ::= <letter> {<letter> | <digit>}
        # type-denoter is technically very flexible because of user-defined types, which are not yet supported,
        # so for right now we will use:
        # <type-denoter> ::= <type-identifier> which will be "integer" | "real" | "Boolean"
        if self.tokenstream.peektokentype() == TokenType.VAR:
            assert isinstance(parent_ast.symboltable, SymbolTable),\
                "Parser.parse_variabledeclarationpart: missing symboltable"
            self.getexpectedtoken(TokenType.VAR)
            done = False
            while not done:
                identifier_list = self.parse_identifierlist()
                self.getexpectedtoken(TokenType.COLON)
                symboltype = self.parse_typeidentifier()
                self.getexpectedtoken(TokenType.SEMICOLON)
                for identifier_token in identifier_list:
                    parent_ast.symboltable.add(VariableSymbol(identifier_token.value,
                                                              identifier_token.location, symboltype))
                if self.tokenstream.peektokentype() != TokenType.IDENTIFIER:
                    done = True
        return None

    def parse_formalparameterlist(self, paramlist):
        # 6.6.3.1 - <formal-parameter-list> ::= "(" <formal-parameter-section> {";" <formal-parameter-section>} ")"
        # 6.6.3.1 - <formal-parameter-section> ::= <value-parameter-specification> | <variable-parameter-specification>
        #                                           | <procedural-parameter-specification>
        #                                           | <functional-parameter-specification>
        # 6.6.3.1 - <value-parameter-specification> ::= <identifier-list> ":" <type-identifier>
        # 6.6.3.1 - <variable-parameter-specification> ::= "var" <identifier-list> ":" <type-identifier>
        # The procedural/funcationl parameter specification are for passing procedures or functions as parameters,
        # which we do not support now.
        assert isinstance(paramlist, ParameterList)

        self.getexpectedtoken(TokenType.LPAREN)

        done = False
        while not done:
            if self.tokenstream.peektokentype() == TokenType.VAR:
                self.getexpectedtoken(TokenType.VAR)
                is_byref = True
            else:
                is_byref = False
            identifier_list = self.parse_identifierlist()
            self.getexpectedtoken(TokenType.COLON)
            symboltype = self.parse_typeidentifier()
            for identifier_token in identifier_list:
                vsym = VariableSymbol(identifier_token.value, identifier_token.location, symboltype)
                vsym.is_byref = is_byref
                paramlist.add(Parameter(vsym, is_byref))
            if self.tokenstream.peektokentype() == TokenType.SEMICOLON:
                self.getexpectedtoken(TokenType.SEMICOLON)
            else:
                done = True
        self.getexpectedtoken(TokenType.RPAREN)

    def parse_procedureandfunctiondeclarationpart(self, parent_ast):
        # returns a list of ASTs, each corresponding to a procedure or function.
        # 6.2.1 - <procedure-and-function-declaration-part> ::= {(<procedure-declaration>|<function-declaration>)";"}
        # 6.6.1 - <procedure-declaration> ::= <procedure-heading> ";" directive
        #                                   | <procedure-identification> ";" <procedure-block>
        #                                   | <procedure-heading> ";" <procedure-block>
        # 6.6.1 - <procedure-heading> ::= "procedure" <identifier> [<formal-parameter-list>]
        # 6.6.1 - <procedure-block> ::= <block>
        # 6.6.2 - <function-declaration> ::= <function-heading> ";" directive
        #                                   | <function-identification> ";" <function-block>
        #                                   | <function-heading> ";" <function-block>
        # 6.6.2 - <function-heading> ::= "function" <identifier> [<formal-parameter-list>] ":" <result-type>
        # 6.6.2 - <result-type> ::= <simple-type-identifier> | <pointer-type-identifier>
        # simple-type-identifier is defined in 6.4.1 and can be any identifier due to user-defined types.
        # So, for now we will use:
        # <simple-type-identifier> ::= <type-identifier> = "integer" | "real" | "boolean"
        # <directive> is defined in 6.1.4 similar to an identifier, but the only directive we will support is "forward"
        #
        # NOTE - there is no closing semicolon in the BNF for procedure-declaration or function-declaration, but
        # I know that the "end" that ends the statement-part of the block must have a semicolon that follows.
        # So we grab it here.

        ret = []
        while self.tokenstream.peektokentype() in [TokenType.PROCEDURE, TokenType.FUNCTION]:
            tok_procfunc = self.tokenstream.eattoken()
            assert isinstance(tok_procfunc, Token)
            ast_procfunc = AST(tok_procfunc, parent_ast)
            ast_procfunc.initsymboltable()
            ast_procfunc.initparamlist()
            tok_procfuncname = self.getexpectedtoken(TokenType.IDENTIFIER)
            ast_procfunc.children.append(AST(tok_procfuncname, ast_procfunc))
            assert isinstance(tok_procfuncname, Token)
            if self.tokenstream.peektokentype() == TokenType.LPAREN:
                self.parse_formalparameterlist(ast_procfunc.paramlist)

            if tok_procfunc.tokentype == TokenType.FUNCTION:
                if self.tokenstream.peektokentype() != TokenType.COLON:
                    # see if the next token is a return type
                    tmp_symboltype = None
                    tmp_token = self.tokenstream.peektoken()
                    try:
                        tmp_symboltype = self.parse_typeidentifier()
                    except ParseException:
                        pass  # errors' are ok here.

                    if tmp_symboltype is None:
                        errstr = "Function {} missing return type at {}".format(tok_procfuncname.value,
                                                                                tok_procfunc.location)
                    else:
                        errstr = "Expected ':' but saw '{}' in {}".format(tmp_token.value, tmp_token.location)
                    raise ParseException(errstr)
                self.getexpectedtoken(TokenType.COLON)
                resulttype = self.parse_typeidentifier()
                # 6.6.2 - functions can only return simple types or pointers
                if not (isinstance(resulttype, pascaltypes.SimpleType) or
                        isinstance(resulttype, pascaltypes.PointerType)):
                    errstr = "Function {} has invalid return type: {} at {}".format(tok_procfuncname.value,
                                                                                    str(resulttype),
                                                                                    str(tok_procfunc.location))
                    raise ParseException(errstr)
                ast_procfunc.symboltable.add(FunctionResultVariableSymbol(tok_procfuncname.value,
                                                                          tok_procfuncname.location,
                                                                          resulttype))
                activationtype = pascaltypes.FunctionType()
            else:
                resulttype = None
                activationtype = pascaltypes.ProcedureType()

            # Procedures and Functions can only be declared in Program scope, or in the scope of other procedures
            # or functions.  So the parent of the procfunc here has to have a symbol table.
            parent_ast.symboltable.add(ActivationSymbol(tok_procfuncname.value, tok_procfuncname.location,
                                                        activationtype, ast_procfunc.paramlist, resulttype))

            self.getexpectedtoken(TokenType.SEMICOLON)
            ast_procfunc.children.extend(self.parse_block(ast_procfunc))
            self.getexpectedtoken(TokenType.SEMICOLON)
            ret.append(ast_procfunc)
        return ret

    def parse_factor(self, parent_ast):
        # 6.7.1 <factor> ::= <variable-access> | <unsigned-constant> | <function-designator> |
        #                    <set-constructor> | "(" <expression> ")" | "not" <factor>
        # 6.7.1 <unsigned-constant> ::= <unsigned-number> | <character-string> | <constant-identifier> | "nil"
        # 6.1.7 <character-string> ::= "'" <string-element> {<string-element>} "'"
        # 6.3 <constant-identifier> ::= <identifier>
        # 6.7.3 <function-designator> ::= <function-identifier> [<actual-parameter-list>]
        # 6.6.2 <function-identifier> ::= <identifier>
        # 6.7.3 <actual-parameter-list> ::= "(" <actual-parameter> {"," <actual-parameter>} ")"

        if self.tokenstream.peektokentype() == TokenType.LPAREN:
            self.getexpectedtoken(TokenType.LPAREN)
            ret = self.parse_expression(parent_ast)
            self.getexpectedtoken(TokenType.RPAREN)
        else:
            if self.tokenstream.peektokentype() == TokenType.UNSIGNED_REAL:
                realtok = self.getexpectedtoken(TokenType.UNSIGNED_REAL)
                self.literaltable.add(NumericLiteral(realtok.value, realtok.location, pascaltypes.RealType()))
                ret = AST(realtok, parent_ast)
            elif self.tokenstream.peektokentype() in (TokenType.UNSIGNED_INT, TokenType.TRUE,
                                                      TokenType.MAXINT, TokenType.FALSE):
                ret = AST(self.tokenstream.eattoken(), parent_ast)
            elif self.tokenstream.peektokentype() == TokenType.CHARSTRING:
                # literalTable.add() allows adding duplicates
                tok_charstr = self.getexpectedtoken(TokenType.CHARSTRING)
                self.literaltable.add(StringLiteral(tok_charstr.value, tok_charstr.location))
                ret = AST(tok_charstr, parent_ast)
            elif is_isorequiredfunction(self.tokenstream.peektokentype()):
                # 6.6.6 in the ISO Standard lists required functions.  All required functions take one
                # argument.  Note, by parsing it this way instead of parsing out the parameter list, we will
                # compile error with a right paren is expected instead of a comma, instead of number of
                # parameters not matching the 1 that is expected.
                ret = AST(self.tokenstream.eattoken(), parent_ast)
                self.getexpectedtoken(TokenType.LPAREN)
                ret.children.append(self.parse_expression(ret))
                self.getexpectedtoken(TokenType.RPAREN)
            elif self.tokenstream.peektokentype() == TokenType.IDENTIFIER:
                # An identifier standalone could either be variable-access, constant-identifier or
                # function-designator with no actual parameter list.  That's fine here, we will disambiguate
                # when generating the TAC. If we see a left paren however, we have the actual parameter list.
                ret = AST(self.tokenstream.eattoken(), parent_ast)
                if self.tokenstream.peektokentype() == TokenType.LPAREN:
                    # now we know it's supposed to be a function-designator.  But, it could be a
                    # procedure by mistake, which would be a compile error.
                    str_procfuncname = ret.token.value
                    # in case of recursion, the actsym will be potentially the return value of a function
                    # instead of an Activation symbol.  But in every other instance, it should be an
                    # activation symbol that we can test.
                    actsym = ret.nearest_symboltable().fetch(str_procfuncname)
                    if isinstance(actsym, ActivationSymbol):
                        if actsym.returnpascaltype is None:
                            errstr = "Procedure {} cannot be used as parameter to {}() in {}"
                            errstr = errstr.format(str_procfuncname, parent_ast.token.value, ret.token.location)
                            raise ParseException(errstr)
                    self.parse_actualparameterlist(ret)
            else:
                errtok = self.tokenstream.eattoken()
                raise ParseException(token_errstr(errtok, "Invalid <unsigned-constant>"))
        return ret

    def parse_term(self, parent_ast):
        # 6.7.1 <term> ::= <factor> { <multiplying-operator> <factor> }
        # 6.7.2.1 <multiplying-operator> ::= "*" | "/" | "div" | "mod" | "and"
        ret = self.parse_factor(parent_ast)
        while ismultiplyingoperator(self.tokenstream.peektokentype()):
            multop = AST(self.tokenstream.eattoken(), parent_ast)
            ret.parent = multop
            multop.children.append(ret)
            multop.children.append(self.parse_factor(multop))
            ret = multop
        return ret

    def parse_simpleexpression(self, parent_ast):
        # 6.7.1 <simple-expression> ::= [sign] <term> { <adding-operator> <term> }
        # 6.1.5 <sign> ::= "+" | "-"
        # 6.7.2.1 <adding-operator> ::= "+" | "-" | "or"

        if self.tokenstream.peektokentype() == TokenType.MINUS:
            # a minus here is identical to multiplying by -1.
            minus = self.getexpectedtoken(TokenType.MINUS)
            ret = AST(Token(TokenType.MULTIPLY, minus.location, ""), parent_ast)
            ret.children.append(AST(Token(TokenType.SIGNED_INT, minus.location, "-1"), ret))
            ret.children.append(self.parse_term(ret))
        else:
            ret = self.parse_term(parent_ast)

        while isaddingoperator(self.tokenstream.peektokentype()):
            addingop = AST(self.tokenstream.eattoken(), parent_ast)
            ret.parent = addingop
            addingop.children.append(ret)
            addingop.children.append(self.parse_term(addingop))
            ret = addingop

        return ret

    def parse_expression(self, parent_ast):
        # 6.7.1 - <expression> ::= <simple-expression> [<relational-operator> <simple-expression>]

        simpleexp1 = self.parse_simpleexpression(parent_ast)
        if isrelationaloperator(self.tokenstream.peektokentype()):
            relationalop = AST(self.tokenstream.eattoken(), parent_ast)
            simpleexp1.parent = relationalop
            relationalop.children.append(simpleexp1)
            relationalop.children.append(self.parse_simpleexpression(relationalop))
            ret = relationalop
        else:
            ret = simpleexp1
        return ret

    def parse_writeandwriteln(self, parent_ast):
        # 6.8.2.3 - <procedure-statement> ::= procedure-identifier ([<actual-parameter-list>] | <read-parameter_list>
        #                                            | <readln-parameter-list> | <write-parameter-list>
        #                                            | <writeln-parameter-list>)
        # 6.6.1 - <procedure-identifier> ::= <identifier>
        # 6.9.3 - <write-parameter-list> ::= "(" [<file-variable> "."] <write-parameter>  {"," <write-parameter>} ")"
        # 6.9.4 - <writeln-parameter-list> ::= "(" [<file-variable> "."] <write-parameter>  {"," <write-parameter>} ")"
        # 6.9.3 - <write-parameter> ::= <expression> [":" <expression> [ ":" <expression> ] ]

        assert self.tokenstream.peektokentype() in (TokenType.WRITE, TokenType.WRITELN), \
            "Parser.parse_writeandwriteln called and write/writeln not next token."

        self.tokenstream.setstartpos()

        ret = AST(self.tokenstream.eattoken(), parent_ast)
        self.getexpectedtoken(TokenType.LPAREN)
        # TODO: When we support other Output types, we need to actually parse the first parameter
        # to see if it is a file-variable.
        # TODO: The file-variable, or implied file-variable OUTPUT should be a symbol.
        if self.tokenstream.peektokentype() == TokenType.OUTPUT:
            # note - the below code will fail because TAC-IR won't know how to parse the OUTPUT token
            ret.children.append(AST(self.getexpectedtoken(TokenType.OUTPUT), parent_ast))
            self.getexpectedtoken(TokenType.COMMA)

        done = False
        while not done:
            ret.children.append(self.parse_expression(ret))
            if self.tokenstream.peektokentype() == TokenType.COMMA:
                self.getexpectedtoken(TokenType.COMMA)
            else:
                done = True
        self.getexpectedtoken(TokenType.RPAREN)
        self.tokenstream.setendpos()
        ret.comment = self.tokenstream.printstarttoend()
        return ret

    def parse_assignmentstatement(self, parent_ast):
        # 6.8.2.2 - <assignment-statement> ::= (<variable-access>|<function-identifier>) ":=" <expression>
        # 6.5.1 - <variable-access> ::= <entire-variable> | <component-variable> | <identified-variable>
        #                               | <buffer-variable>
        # 6.5.2 - <entire-variable> ::= <variable-identifier>
        # 6.5.2 - <variable-identifier> ::= <identifier>
        nexttwo = self.tokenstream.peekmultitokentype(2)
        assert nexttwo[0] == TokenType.IDENTIFIER, "Parser.parse_assignmentstatement called, identifier not next token."
        assert nexttwo[1] == TokenType.ASSIGNMENT, "Parser.parse_assignmentstatement called without assignment token."
        assert parent_ast is not None

        self.tokenstream.setstartpos()
        ident_token = self.getexpectedtoken(TokenType.IDENTIFIER)

        # validate that we are assigning to a valid identifier - either a symbol or a parameter
        symtab = parent_ast.nearest_symboltable()
        if not symtab.existsanywhere(ident_token.value):
            tmp_ast = parent_ast
            tmp_paramlist = tmp_ast.paramlist
            while tmp_paramlist is None:
                assert isinstance(tmp_ast, AST)
                if tmp_ast.parent is None:
                    # we made it to the top of the AST without finding a param list.  Since
                    errstr = "Undefined Identifier: {} in {}".format(ident_token.value, ident_token.location)
                    raise ParseException(errstr)
                tmp_ast = tmp_ast.parent
                tmp_paramlist = tmp_ast.paramlist
            assert isinstance(tmp_paramlist, ParameterList)
            param = tmp_paramlist.fetch(ident_token.value)
            if param is None:
                raise ParseException("Undefined Identifier: {} in {}".format(ident_token.value, ident_token.location))
            else:
                assert isinstance(param, Parameter)
        else:
            sym = symtab.fetch(ident_token.value)
            if isinstance(sym, ConstantSymbol):
                errstr = "Cannot assign to constant '{}' in {}".format(ident_token.value, ident_token.location)
                raise ParseException(errstr)
            assert isinstance(sym, VariableSymbol)  # we insert a FunctionResultVariableSymbol when parsing functions

        # Two possible designs considered here.  First, having ret have some token that represents
        # the variable-identifier and that it is being assigned to, and then have one child which
        # is the expression, or the one that I'm going with here, which is to have ret explicitly
        # be the assign operation with first child the variable being assigned and second child
        # being the expression.  I don't know that either is better but this seemed cleaner
        # because it put all the tokens in the AST and did not require creation of a new tokentype
        # like I did in first compiler.
        ret = AST(self.getexpectedtoken(TokenType.ASSIGNMENT), parent_ast)
        ret.children.append(AST(ident_token, ret))
        ret.children.append(self.parse_expression(ret))
        self.tokenstream.setendpos()
        ret.comment = self.tokenstream.printstarttoend()
        return ret

    def parse_gotostatement(self, parent_ast):
        assert parent_ast is not None
        assert self.tokenstream.peektokentype() == TokenType.GOTO, "Parser_parse_gotostatement called without goto"
        raise ParseException(token_errstr(self.tokenstream.eattoken()), "goto not handled at this time")

    def parse_actualparameterlist(self, parent_ast):
        # 6.7.3 - <actual-parameter-list> ::= "(" <actual-parameter> {"," <actual-parameter>} ")"
        # 6.7.3 - <actual-parameter> ::= <expression> | <variable-access> | <procedure-identifier>
        #                                   | <function-identifier>
        # 6.6.1 - <procedure-identifier> ::= <identifier>
        # 6.6.2 - <function-identifier> ::= <identifier>
        # 6.5.1 - <variable-access> ::= <entire-variable> | <component-variable> | <identified-variable>
        #                               | <buffer-variable>
        # 6.5.2 - <entire-variable> ::= <variable-identifier>
        # 6.5.2 - <variable-identifier> ::= <identifier>

        # This function appends each parameter to the parent_ast as a child.

        # The <procedure-identifier> and <function-identifier> are for passing in procedures and functions
        # as parameters.  We do not support that yet.  Passing the value of a function in as a parameter
        # would come from the <factor> which in turn comes from the <expression>.

        # note there is a weird corner case here.  Look at the following snippet:
        # var i:integer;
        #
        # function a():integer;  {this is a function that takes no parameters}
        #   ...
        # function b(x:integer):integer;
        #   ...
        # function c(function q():integer):integer;
        #
        # begin
        #   i:=a;   {this computes a and stores the result in i.  This is unlike C where it would be i=a();}
        #   i:=b(a);  {this computes a, takes the result and passes it in as a parameter to b}
        #   i:=c(a);  {this passes the function a as a parameter to c}
        # end.
        #
        # You can't tell the difference between i:=b(a) and i:=c(a) without looking at the parameter lists for b and c.
        # However, the AST for both will be the same - b or c as identifiers with a single child with a as an
        # identifier.  The AST will be interpreted when generating the TAC, because at that time the parsing pass has
        # been completed and all the symbol tables will have been built and can be queried.
        assert isinstance(parent_ast, AST)

        self.getexpectedtoken(TokenType.LPAREN)
        done = False
        while not done:
            parent_ast.children.append(self.parse_expression(parent_ast))
            if self.tokenstream.peektokentype() == TokenType.COMMA:
                self.getexpectedtoken(TokenType.COMMA)
            else:
                done = True
        self.getexpectedtoken(TokenType.RPAREN)

    def parse_procedurestatement(self, parent_ast):
        # 6.8.2.3 - <procedure-statement> ::= procedure-identifier ([<actual-parameter-list>] | <read-parameter_list>
        #                                            | <readln-parameter-list> | <write-parameter-list>
        #                                            | <writeln-parameter-list>)
        # 6.6.1 - <procedure-identifier> ::= <identifier>
        assert self.tokenstream.peektokentype() == TokenType.IDENTIFIER, \
            "Parser.parseprocedurestatement called and identifier not next token."

        # TODO - fix the setstartpos/setendpos so that comments can nest, and we can get the comments for
        # code inside the parameter list parsing.  For now, cannot do that.
        self.tokenstream.setstartpos()
        ret = AST(self.getexpectedtoken(TokenType.IDENTIFIER), parent_ast)
        self.tokenstream.setendpos()
        ret.comment = "Call procedure: {}".format(self.tokenstream.printstarttoend())
        self.parse_actualparameterlist(ret)
        return ret

    def parse_simplestatement(self, parent_ast):
        # 6.8.2.1 - <simple-statement> ::= <empty-statement> | <assignment-statement> | <procedure-statement>
        #                                   | <goto-statement>
        # 6.8.2.3 - <procedure-statement> ::= procedure-identifier ([<actual-parameter-list>] | <read-parameter_list>
        #                                            | <readln-parameter-list> | <write-parameter-list>
        #                                            | <writeln-parameter-list>)
        # 6.6.1 - <procedure-identifier> ::= <identifier>
        # 6.8.2.2 - <assignment-statement> ::= (<variable-access>|<function-identifier>) ":=" <expression>
        # 6.5.1 - <variable-access> ::= <entire-variable> | <component-variable> | <identified-variable>
        #                               | <buffer-variable>
        # 6.5.2 - <entire-variable> ::= <variable-identifier>
        # 6.5.2 - <variable-identifier> ::= <identifier>
        assert parent_ast is not None

        next_tokentype = self.tokenstream.peektokentype()

        if next_tokentype in (TokenType.WRITE, TokenType.WRITELN):
            return self.parse_writeandwriteln(parent_ast)
        elif next_tokentype == TokenType.GOTO:
            return self.parse_gotostatement(parent_ast)
        elif next_tokentype == TokenType.IDENTIFIER:
            nexttwo = self.tokenstream.peekmultitokentype(2)
            if nexttwo[1] == TokenType.ASSIGNMENT:
                return self.parse_assignmentstatement(parent_ast)
            else:
                next_tokenname = self.tokenstream.peektoken().value
                try:
                    sym = parent_ast.nearest_symboltable().fetch(next_tokenname)
                except SymbolException:
                    raise ParseException(token_errstr(self.tokenstream.peektoken(), "Identifier undefined"))
                if isinstance(sym, ActivationSymbol):
                    return self.parse_procedurestatement(parent_ast)
                else:
                    tok = self.tokenstream.eattoken()
                    if self.tokenstream.peektokentype() == TokenType.EQUALS:
                        errstr = "Identifier '{}' followed by '=' seen at {}, was assignment intended?"
                        errstr = errstr.format(tok.value, tok.location)
                    else:
                        errstr = "Identifier '{}' seen at {}, unclear how to parse".format(tok.value, tok.location)
                    raise ParseException(errstr)
        else:
            raise ParseException(token_errstr(self.tokenstream.eattoken()))

    def parse_ifstatement(self, parent_ast):
        # 6.8.3.4 <if-statement> ::= "if" <Boolean-expression> "then" <statement> [else-part]
        # 6.8.3.4 <else-part> ::= "else" <statement>
        # 6.7.2.3 <Boolean-expression> ::= <expression>
        assert self.tokenstream.peektokentype() == TokenType.IF, \
            "Parser.parse_ifstatement called and 'if' not next token."

        self.tokenstream.setstartpos()
        ret = AST(self.tokenstream.eattoken(), parent_ast)
        ret.children.append(self.parse_expression(ret))
        self.getexpectedtoken(TokenType.THEN)
        self.tokenstream.setendpos()
        # this makes the comment "If <condition> Then" which is fine.
        ret.comment = self.tokenstream.printstarttoend()

        ret.children.append(self.parse_statement(ret))
        if self.tokenstream.peektokentype() == TokenType.ELSE:
            self.getexpectedtoken(TokenType.ELSE)
            # The comment "ELSE" is added in tac_ir.py - that is a bit hacky but it works
            # TODO - figure out if I can add a comment "ELSE" here and remove that one.
            ret.children.append(self.parse_statement(ret))
        return ret

    def parse_conditionalstatement(self, parent_ast):
        # 6.8.3.3 - <conditional-statement> ::= <if-statement> | <case-statement>
        return self.parse_ifstatement(parent_ast)

    def parse_whilestatement(self, parent_ast):
        # 6.8.3.8 - <while-statement> ::= "while" <Boolean-expression> "do" <statement>
        # 6.7.2.3 - <Boolean-expression> ::= <expression>
        assert self.tokenstream.peektokentype() == TokenType.WHILE, \
            "Parser.parse_whilestatement called and 'while' not next token."

        self.tokenstream.setstartpos()
        ret = AST(self.tokenstream.eattoken(), parent_ast)
        ret.children.append(self.parse_expression(ret))
        self.getexpectedtoken(TokenType.DO)
        self.tokenstream.setendpos()
        # this makes the comment "while <condition> do" which is fine.
        ret.comment = self.tokenstream.printstarttoend()

        ret.children.append(self.parse_statement(ret))
        return ret

    def parse_repeatstatement(self, parent_ast):
        # 6.8.3.7 - <repeat-statement> ::= "repeat" <statement-sequence> "until" <Boolean-expression>
        # 6.7.2.3 - <Boolean-expression> ::= <expression>
        assert self.tokenstream.peektokentype() == TokenType.REPEAT, \
            "Parser.parse_repeatstatement called and 'repeat' not next token."

        self.tokenstream.setstartpos()
        ret = AST(self.tokenstream.eattoken(), parent_ast)
        self.tokenstream.setendpos()
        repeatcomment = self.tokenstream.printstarttoend()

        self.parse_statementsequence(TokenType.UNTIL, ret)

        self.tokenstream.setstartpos()
        self.getexpectedtoken(TokenType.UNTIL)
        ret.children.append(self.parse_expression(ret))
        self.tokenstream.setendpos()
        untilcomment = self.tokenstream.printstarttoend()
        # comment will be "repeat until <condition>"
        ret.comment = "{0} {1}".format(repeatcomment, untilcomment)
        return ret

    def parse_repetitivestatement(self, parent_ast):
        # 6.8.3.6 - <repetitive-statement> ::= <repeat-statement> | <while-statement> | <for-statement>
        assert self.tokenstream.peektokentype() in (TokenType.WHILE, TokenType.REPEAT, TokenType.FOR), \
            "Parser.parse_repetitivestatement: called for token that is not While, Repeat, or For"

        # while and repeat are supported
        if self.tokenstream.peektokentype() == TokenType.WHILE:
            ret = self.parse_whilestatement(parent_ast)
        elif self.tokenstream.peektokentype() == TokenType.REPEAT:
            ret = self.parse_repeatstatement(parent_ast)
        else:
            ret = None  # we don't handle FOR yet
        return ret

    def parse_structuredstatement(self, parent_ast):
        # 6.8.3.1 - <structured-statement> ::= <compound-statement> | <conditional-statement>
        #                                       | <repetitive-statement> | <with-statement>

        # with-statement is not currently supported.
        # while-statement and repeat-statement are the repetitive statements supported.

        if self.tokenstream.peektokentype() == TokenType.BEGIN:
            return self.parse_compoundstatement(parent_ast)
        elif self.tokenstream.peektokentype() in (TokenType.WHILE, TokenType.REPEAT):
            return self.parse_repetitivestatement(parent_ast)
        else:
            return self.parse_conditionalstatement(parent_ast)

    def parse_statement(self, parent_ast):
        # 6.8.1 - <statement> ::= [<label>:] (<simple-statement> | <structured-statement>)
        # labels are not yet supported
        assert parent_ast is not None

        next_tokentype = self.tokenstream.peektokentype()
        # TODO make a helper function to see if next token type makes for a structured statement
        if startsstructuredstatement(next_tokentype):
            return self.parse_structuredstatement(parent_ast)
        else:
            return self.parse_simplestatement(parent_ast)

    def parse_statementsequence(self, endtokentype, current_ast):
        # 6.8.3.1 - <statement-sequence> ::= <statement> [ ";" <statement> ]

        # statement sequences are, as they are named, sequences of statements.  However,
        # the end of the sequence is denoted by different tokens depending on where the
        # statement sequence is embedded.  Two examples are compound-statement, which is
        # "begin" <statement-sequence> "end" and the repeat-statement, which is
        # "repeat" <statement-sequence> "until."

        # current_ast is the location where the children should be added
        current_ast.children.append(self.parse_statement(current_ast))
        while self.tokenstream.peektokentype() == TokenType.SEMICOLON:
            self.getexpectedtoken(TokenType.SEMICOLON)
            if self.tokenstream.peektokentype() != endtokentype:
                current_ast.children.append(self.parse_statement(current_ast))
            if self.tokenstream.peektokentype() != TokenType.SEMICOLON \
                    and self.tokenstream.peektokentype() != endtokentype:
                # TODO - insert a semicolon into the stream and allow parsing to continue
                # special case error if we don't see the end token and don't see a semicolon
                nexttok = self.tokenstream.peektoken()
                raise ParseException("Semicolon expected in {}".format(nexttok.location))

    def parse_compoundstatement(self, parent_ast):
        # 6.8.3.2 - <compound-statement> ::= "begin" <statement-sequence> "end"
        # This function returns an AST node using the BEGIN as the token, and with one child for each
        # statement.
        ret = AST(self.getexpectedtoken(TokenType.BEGIN), parent_ast)
        self.parse_statementsequence(TokenType.END, ret)

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

    def parse_statementpart(self, parent_ast):
        # 6.2.1 defines statement-part simply as <statement-part> ::= <compound-statement>

        # The <statement-part> is the only portion of the <block> that is required.  Each of the
        # other parts, i.e. label declaration, constant definition, type definition, variable declaration
        # and procedure/function declaration are optional.
        return self.parse_compoundstatement(parent_ast)

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
            ret.extend(a)

        # parse_constantdefinitionpart updates the literal and symbol tables, does not return anything to add to AST.
        self.parse_constantdefinitionpart(parent_ast)

        a = self.parse_typedefinitionpart(parent_ast)
        if a is not None:
            ret.extend(a)

        # parse_variabledeclarationpart updates the symbol table, it does not return anything to be added to the AST.
        self.parse_variabledeclarationpart(parent_ast)

        a = self.parse_procedureandfunctiondeclarationpart(parent_ast)
        if a is not None:
            ret.extend(a)
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
        ret.initsymboltable()
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
