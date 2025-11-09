from lexer import TokenType, Token, TokenStream, LexerException
from symboltable import StringLiteral, LiteralTable, SymbolTable, VariableSymbol, ParameterList, \
    ActivationSymbol, FunctionResultVariableSymbol, Parameter, SymbolException, ConstantSymbol, RealLiteral, \
    CharacterLiteral, ProgramParameterSymbol
from compiler_error import compiler_errstr
from copy import deepcopy
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

    def initsymboltable(self):
        self.symboltable = SymbolTable()

        if self.parent is None:
            # root of the tree gets the type identifiers for the required types
            self.symboltable.addsimpletypes()
        else:
            # every other symbol table has to have a pointer to its parent, and there must be a parent
            # since the root has a symboltable and this is not the root.
            ptr = self.parent
            while ptr.symboltable is None:
                ptr = ptr.parent
                # the root of the AST has a symboltable for globals, so since this node is not the root
                # it should never get to None.
                assert ptr is not None, "AST.initsymboltable: No symboltable in AST ancestry"
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

    def nearest_symboldefinition(self, symbolname):
        # returns the nearest symbol with a given identifier, None if the symbol is not defined.
        # checks the local symbol table, then the local parameter list, then goes to the parent ast
        # and repeats, until symbol is found, or the top of the tree is reached.

        ptr = self
        ret = None
        while ptr is not None and ret is None:
            if ptr.symboltable is not None and ptr.symboltable.exists(symbolname):
                ret = ptr.symboltable.fetch(symbolname)  # errors if not found, hence testing exists()
            elif ptr.paramlist is not None:
                param = ptr.paramlist.fetch(symbolname)  # returns None if not found
                if param is not None:
                    ret = param.symbol
            ptr = ptr.parent
        return ret

    def nearest_paramlist(self):
        # returns None if no paramlist above this node in the tree, meaning the statement is outside
        # a procedure or function.
        # TODO - where this is used, we will have a problem with nested procs/funcs.
        ptr = self
        while ptr is not None and ptr.paramlist is None:
            ptr = ptr.parent
        if ptr is None:
            return None
        else:
            return ptr.paramlist

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
        self.anonymous_type_counter = 0

    def getexpectedtoken(self, tokentype):
        assert(isinstance(tokentype, TokenType)), "Parser.getexpectedtoken: Expected Token must be a token"
        ret = self.tokenstream.eattoken()
        if ret.tokentype != tokentype:
            if tokentype == TokenType.SEMICOLON:
                # TODO - insert a semicolon into the stream and allow parsing to continue
                # TODO - this needs a test case.
                errstr = compiler_errstr("Semicolon expected",self.tokenstream.peekprevioustoken())
            else:
                errstr = compiler_errstr("Expected '{0}' but saw '{1}'".format(str(tokentype), str(ret.value)),
                                         ret)
            raise ParseException(errstr)
        assert isinstance(ret, Token)
        return ret

    def parse_labeldeclarationpart(self, parent_ast):
        return None

    def parse_constant(self, parent_ast, optionalconstid=""):
        # returns a tuple (type of the constant, value of the constant)
        # value of the constant will be a string
        # optionalconstid is if you are using this to parse a constant definition, it enables us to catch
        # a self-referencing constant definition.
        #
        # 6.3 <constant> ::= [sign] (<unsigned-number> | <constant-identifier>) | <character-string>
        # 6.1.5 <sign> ::= "+" | "-"
        # 6.3 <constant-identifier> ::= <identifier>
        # 6.1.7 <character-string> ::= "'" <string-element> {<string-element>} "'"
        #
        # p.65 of [Cooper] states that if a constant has a sign then the next token must be
        # a real, an integer, or a real/integer constant.  That can't be captured in the BNF.

        ret = None  # this is to avoid PyCharm flagging that ret may not be assigned before it's used

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
            self.literaltable.add(RealLiteral(tokval, realtok.location))
            ret = pascaltypes.RealType(), tokval
        elif self.tokenstream.peektokentype() == TokenType.UNSIGNED_INT:
            inttok = self.getexpectedtoken(TokenType.UNSIGNED_INT)
            if isneg:
                tokval = "-" + inttok.value
            else:
                tokval = inttok.value
            ret = pascaltypes.IntegerType(), tokval
        elif self.tokenstream.peektokentype() == TokenType.MAXINT:
            self.getexpectedtoken(TokenType.MAXINT)
            if isneg:
                ret = pascaltypes.IntegerType(), pascaltypes.STRNEGMAXINT
            else:
                ret = pascaltypes.IntegerType(), pascaltypes.STRMAXINT
        elif self.tokenstream.peektokentype() in (TokenType.TRUE, TokenType.FALSE):
            booltok = self.tokenstream.eattoken()
            if sawsign:
                errstr = compiler_errstr("Cannot have a sign before a Boolean constant", booltok)
                raise ParseException(errstr)
            ret = pascaltypes.BooleanType(), booltok.value
        elif self.tokenstream.peektokentype() == TokenType.CHARSTRING:
            charstrtok = self.getexpectedtoken(TokenType.CHARSTRING)
            if sawsign:
                errstr = compiler_errstr("Cannot have a sign before a string constant",charstrtok)
                raise ParseException(errstr)
            if len(charstrtok.value) == 1:
                self.literaltable.add(CharacterLiteral(charstrtok.value, charstrtok.location))
                ret = pascaltypes.CharacterType(), charstrtok.value
            else:
                self.literaltable.add(StringLiteral(charstrtok.value, charstrtok.location))
                ret = pascaltypes.StringLiteralType(), charstrtok.value
        elif self.tokenstream.peektokentype() == TokenType.IDENTIFIER:
            ident_token = self.getexpectedtoken(TokenType.IDENTIFIER)
            if not parent_ast.symboltable.existsanywhere(ident_token.value):
                if ident_token.value == optionalconstid:
                    errstr = compiler_errstr("Self-referencing constant definition '{}'".format(ident_token.value), ident_token)
                else:
                    errstr = compiler_errstr("Undefined Identifier: '{}'".format(ident_token.value), ident_token)
                raise ParseException(errstr)
            sym = parent_ast.symboltable.fetch(ident_token.value)
            if not isinstance(sym, ConstantSymbol) and not isinstance(sym, pascaltypes.EnumeratedTypeValue):
                if optionalconstid != "":
                    errstr = "Constant '{}' must be defined as a literal or another constant, cannot use '{}'"
                    errstr = errstr.format(optionalconstid, ident_token.value)
                else:
                    errstr = "Constant expected, must be literal or another constant, cannot use '{}'"
                    errstr = errstr.format(ident_token.value)
                errstr = compiler_errstr(errstr, ident_token)
                raise ParseException(errstr)
            if sawsign:
                invalidsign = False
                if isinstance(sym, pascaltypes.EnumeratedTypeValue):
                    invalidsign = True
                else:
                    assert isinstance(sym, ConstantSymbol)

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
                                self.literaltable.add(RealLiteral(tokval, ident_token.location))
                                ret = sym.pascaltype, tokval
                            else:
                                ret = sym.pascaltype, tokval
                        else:
                            tokval = sym.value
                            ret = sym.pascaltype, tokval
                    else:
                        invalidsign = True

                if invalidsign:
                    errstr = "Constant '{}' is not numeric."
                    if optionalconstid != "":
                        errstr += " Cannot define constant '{}' ".format(optionalconstid)
                    else:
                        errstr += " Cannot define constant "
                    errstr += "by putting a sign before a non-numeric constant."
                    errstr = errstr.format(ident_token.value)
                    raise ParseException(compiler_errstr(errstr, ident_token))
            elif isinstance(sym, pascaltypes.EnumeratedTypeValue):
                enumerated_type = parent_ast.symboltable.fetch_originalsymtable_andtype(sym.typeidentifier)[1]
                ret = enumerated_type, ident_token.value
            else:
                assert isinstance(sym, ConstantSymbol)
                tokval = sym.value
                ret = sym.pascaltype, tokval
        else:
            nexttok = self.tokenstream.eattoken()
            errstr = "Unexpected token {}".format(str(nexttok.value))
            raise ParseException(compiler_errstr(errstr, nexttok))

        assert ret is not None  # None isn't valid, but we assigned to None to avoid ret not assigned warning below
        return ret

    def parse_constantdefinitionpart(self, parent_ast):
        # 6.2.1 <constant-definition-part> ::= [ "const" <constant-definition> ";" {<constant-definition> ";"} ]
        # 6.3 <constant-definition> ::= <identifier> "=" <constant>

        if self.tokenstream.peektokentype() == TokenType.CONST:
            assert isinstance(parent_ast.symboltable, SymbolTable), \
                "Parser.parse_constantdefinitionpart: missing symboltable"
            self.getexpectedtoken(TokenType.CONST)
            done = False
            while not done:
                const_id = self.getexpectedtoken(TokenType.IDENTIFIER)
                self.getexpectedtoken(TokenType.EQUALS)
                consttype, constval = self.parse_constant(parent_ast, const_id.value)
                if isinstance(consttype, pascaltypes.RealType):
                    newsymtype = pascaltypes.RealType()
                elif isinstance(consttype, pascaltypes.IntegerType):
                    newsymtype = pascaltypes.IntegerType()
                elif isinstance(consttype, pascaltypes.BooleanType):
                    newsymtype = pascaltypes.BooleanType()
                elif isinstance(consttype, pascaltypes.CharacterType):
                    newsymtype = pascaltypes.CharacterType()
                elif isinstance(consttype, pascaltypes.StringLiteralType):
                    newsymtype = pascaltypes.StringLiteralType()
                else:
                    newsymtype = consttype
                parent_ast.symboltable.add(ConstantSymbol(const_id.value, const_id.location, newsymtype, constval))
                self.getexpectedtoken(TokenType.SEMICOLON)
                if self.tokenstream.peektokentype() != TokenType.IDENTIFIER:
                    done = True

        return None

    def next_three_tokens_contain_subrange(self):
        # 6.4.2.4 <subrange-type> ::= <constant> ".." <constant>
        # So we have a subrange if the token two ahead contains a subrange token, or the token 3 ahead
        # contains a subrange token.  Hard to write in a single line, legibly, so I broke it out.
        next3 = self.tokenstream.peekmultitokentype(3)
        if next3[1] == TokenType.SUBRANGE or next3[2] == TokenType.SUBRANGE:
            return True
        else:
            return False

    def parse_typedefinitionpart(self, parent_ast):
        # 6.2.1 <type-definition-part> ::= ["type" <type-definition> ";" {<type-definition> ";"} ]
        # 6.4.1 <type-definition> ::= <identifier> "=" <type-denoter>

        if self.tokenstream.peektokentype() == TokenType.TYPE:
            assert isinstance(parent_ast.symboltable, SymbolTable), \
                "Parser.parse_typedeclarationpart: missing symboltable"

            self.getexpectedtoken(TokenType.TYPE)
            done = False
            while not done:
                identifier = self.getexpectedtoken(TokenType.IDENTIFIER)
                self.getexpectedtoken(TokenType.EQUALS)
                self.parse_typedenoter(parent_ast, identifier)
                self.getexpectedtoken(TokenType.SEMICOLON)
                if self.tokenstream.peektokentype() != TokenType.IDENTIFIER:
                    done = True

    def parse_typeidentifier(self, parent_ast):
        # 6.4.1 <type-identifier> ::= <identifier>
        #   The valid type-identifiers are the simple types (integer, char, boolean, real), file types and identifiers
        #   that have already been defined for other types.
        #
        # Returns a type

        type_token = self.tokenstream.eattoken()
        if type_token.tokentype not in (TokenType.INTEGER, TokenType.REAL, TokenType.BOOLEAN,
                                        TokenType.CHAR, TokenType.TEXT, TokenType.IDENTIFIER):
            errstr = "Invalid type identifier '{}'".format(type_token.value)
            raise ParseException(compiler_errstr(errstr, type_token))

        if type_token.tokentype == TokenType.IDENTIFIER:
            symboltype = parent_ast.symboltable.fetch(type_token.value)
        else:
            symboltype = parent_ast.symboltable.fetch(str(type_token.tokentype))
        if not isinstance(symboltype, pascaltypes.BaseType):
            raise ParseException(compiler_errstr("Invalid type identifier '{}'".format(type_token.value), type_token))
        return symboltype

    def generate_anonymous_typeidentifier(self):
        # begins with an underscore so can never clash with a valid pascal identifier.
        ret = "_anonymous_{}".format(str(self.anonymous_type_counter))
        self.anonymous_type_counter += 1
        return ret

    def parse_subrangetype(self, parent_ast, optionaltypeidentifiertok=None):
        # 6.4.2.4 <subrange-type> ::= <constant> ".." <constant>
        # 6.3 <constant> ::= [sign](<unsigned-number> | <constant-identifier>) | <character-string>
        #   (character-string is not valid for subrange types, however)
        #
        # Note that the text of 6.4.2.4 states that "Both constants shall be of the same ordinal type,"
        # even though <unsigned-number> allows for integers or reals.
        #
        # This function returns the type.  If a <new-type> is created, then the <new-type> will be
        # added to the symbol table.  The name of the new type will be in the optionaltypename field.
        # If a <new-type> is created and the typename is blank, then the type name will be created
        # anonymously.  See page 69 of Cooper for discussion of anonymous types.

        assert self.next_three_tokens_contain_subrange()

        optionaltypeidentifier = ""
        if optionaltypeidentifiertok is not None:
            optionaltypeidentifier = optionaltypeidentifiertok.value

        nexttok = self.tokenstream.peektoken()  # used for error messages
        const1type, const1value = self.parse_constant(parent_ast)
        self.getexpectedtoken(TokenType.SUBRANGE)
        const2type, const2value = self.parse_constant(parent_ast)
        if not parent_ast.symboltable.are_same_type(const1type.identifier, const2type.identifier):
            errstr = "Both elements of subrange type {} must be same type."
            errstr += "'{}' is type {} and '{}' is type {}"
            # optionaltypename may be blank here, and that's ok for the error message, rather than
            # plugging in an anonymous type
            errstr = errstr.format(optionaltypeidentifier, const1value, const1type.identifier,
                                   const2value, const2type.identifier)
            raise ParseException(compiler_errstr(errstr, nexttok))

        if not isinstance(const1type, pascaltypes.OrdinalType) or not isinstance(const2type, pascaltypes.OrdinalType):
            errstr = "Both elements of subrange type {} must be ordinal type."
            errstr += " Types {} and {} are used"
            errstr = errstr.format(optionaltypeidentifier, const1type.identifier, const2type.identifier)
            raise ParseException(compiler_errstr(errstr, nexttok))

        if optionaltypeidentifier == "":
            typeidentifier = self.generate_anonymous_typeidentifier()
        else:
            typeidentifier = optionaltypeidentifier

        try:
            ret = pascaltypes.SubrangeType(typeidentifier, const1type, const1value, const2value)
        except pascaltypes.PascalTypeException as e:
            raise ParseException(compiler_errstr(e, nexttok))

        parent_ast.symboltable.add(ret)
        return ret

    def parse_enumeratedtype(self, parent_ast, optionaltypenametok=None):
        # 6.4.2.3 <enumerated-type> ::= "(" <identifier-list> ")"
        # 6.4.2.3 <identifier-list> ::= <identifier> {"," <identifier>}
        #
        # This function returns the type.  If a <new-type> is created, then the <new-type> will be
        # added to the symbol table.  The name of the new type will be in the optionaltypename field.
        # If a <new-type> is created and the typename is blank, then the type name will be created
        # anonymously.  See page 69 of Cooper for discussion of anonymous types.

        self.getexpectedtoken(TokenType.LPAREN)

        if optionaltypenametok is None:
            typename = self.generate_anonymous_typeidentifier()
        else:
            typename = optionaltypenametok.value

        idlist = self.parse_identifierlist()
        etvlist = []
        for idtoken in idlist:
            newetv = pascaltypes.EnumeratedTypeValue(idtoken.value, typename, len(etvlist))
            etvlist.append(newetv)
            try:
                parent_ast.symboltable.add(newetv)
            except SymbolException:
                errstr = compiler_errstr("Identifier redefined: '{}'".format(idtoken.value), idtoken)
                raise ParseException(errstr)

        try:
            ret = pascaltypes.EnumeratedType(typename, etvlist)
        except pascaltypes.PascalTypeException as e:
            raise ParseException(compiler_errstr(e, optionaltypenametok))
        self.getexpectedtoken(TokenType.RPAREN)

        parent_ast.symboltable.add(ret)
        return ret

    def parse_indextype_list(self, parent_ast):
        # 6.4.3.2 <array-type> ::= "array" "[" <index-type> {"," <index-type>} "]" "of" <component-type>
        # 6.4.3.2 <index-type> ::= <ordinal-type>
        # 6.4.2.1 <ordinal-type> ::= <new-ordinal-type> | <ordinal-type-identifier>
        # 6.4.2.1 <new-ordinal-type> ::= <enumerated-type> | <subrange-type>
        #
        # returns a list of types
        ret = []
        done = False

        while not done:
            tmptok = self.tokenstream.peektoken()  # used for error messages
            newtype = self.parse_typedenoter(parent_ast)
            if not isinstance(newtype, pascaltypes.OrdinalType):
                raise ParseException(compiler_errstr("Invalid type for array index '{}'".format(tmptok.value), tmptok))
            ret.append(newtype)
            if self.tokenstream.peektokentype() == TokenType.COMMA:
                self.getexpectedtoken(TokenType.COMMA)
            else:
                done = True
        return ret

    def parse_structuredtype(self, parent_ast, optionaltypeidentifiertok=None):
        # 6.4.3.1 <new-structured-type> ::= ["packed"] <unpacked-structured-type>
        # 6.4.3.1 <unpacked-structured-type> ::= <array-type> | <record-type> | <set-type> | <file-type>
        # 6.4.3.2 <array-type> ::= "array" "[" <index-type> {"," <index-type>} "]" "of" <component-type>
        # 6.4.3.2 <index-type> ::= <ordinal-type>
        # 6.4.2.1 <ordinal-type> ::= <new-ordinal-type> | <ordinal-type-identifier>
        # 6.4.2.1 <new-ordinal-type> ::= <enumerated-type> | <subrange-type>
        # 6.4.3.2 <component-type> ::= <type-denoter>
        #
        # This function returns the type.  If a <new-type> is created, then the <new-type> will be
        # added to the symbol table.  The name of the new type will be in the optionaltypename field.
        # If a <new-type> is created and the typename is blank, then the type name will be created
        # anonymously.  See page 69 of Cooper for discussion of anonymous types.
        #
        # Note that both the index types and the component type can be defined anonymously, as well as the
        # array type which we are parsing.
        #
        # Also note, in 6.4.3.2 of the ISO standard, it states that an Array type that specifies 2 or more
        # index types shall be viewed as shorthand for an array that has the first index type as its index
        # type, containing other arrays.  Thus, we will represent arrays that way in our system.  Reason
        # is that these types are the same type when it comes to type compatibility, assume "size" is an
        # ordinal type:
        #
        #       array [Boolean] of array [1..10] of array [size] of real
        #       array [Boolean] of array [1..10, size] of real
        #       array [Boolean, 1..10, size] of real
        #       array [Boolean, 1..10] of array [size] of real
        #
        optionaltypeidentifier = ""
        if optionaltypeidentifiertok is not None:
            optionaltypeidentifier = optionaltypeidentifiertok.value

        if self.tokenstream.peektokentype() == TokenType.PACKED:
            self.getexpectedtoken(TokenType.PACKED)
            ispacked = True
        else:
            ispacked = False

        if self.tokenstream.peektokentype() == TokenType.ARRAY:

            self.getexpectedtoken(TokenType.ARRAY)
            self.getexpectedtoken(TokenType.LBRACKET)
            indextypelist = self.parse_indextype_list(parent_ast)
            self.getexpectedtoken(TokenType.RBRACKET)
            self.getexpectedtoken(TokenType.OF)
            component_type = self.parse_typedenoter(parent_ast)

            # iterate through the indextype list backwards.

            nexttype = component_type
            for i in range(-1, (-1 * len(indextypelist)) - 1, -1):
                indextype = indextypelist[i]
                # the typename passed into this function goes to the outermost array definition.
                # If it is shorthand for multiple arrays, then the inner array definitions are all
                # anonymously named.
                if i == (-1 * len(indextypelist)) and optionaltypeidentifier != "":
                    typeidentifier = optionaltypeidentifier
                else:
                    typeidentifier = self.generate_anonymous_typeidentifier()

                # the nexttype variable will be overwritten every type through the loop, so only
                # the final one processed will be returned
                nexttype = pascaltypes.ArrayType(typeidentifier, indextype, nexttype, ispacked)
                parent_ast.symboltable.add(nexttype)
            return nexttype

        else:
            tok = self.tokenstream.eattoken()
            raise ParseException(compiler_errstr("Invalid Structured Type {}".format(tok.value), tok))

    def parse_typedenoter(self, parent_ast, optionaltypeidentifiertok=None):
        # 6.4.1 <type-denoter> ::= <type-identifier> | <new-type>
        # 6.4.1 <type-identifier> ::= <identifier>
        #   The valid type-identifiers are the simple types (integer, char, boolean, real) and identifiers
        #   that have already been defined for other types.
        # 6.4.1 <new-type> ::= <new-ordinal-type> | <new-structured-type> | <new-pointer-type>
        # 6.4.2.1 <new-ordinal-type> ::= <enumerated-type> | <subrange-type>
        # 6.4.3.1 <new-structured-type> ::= ["packed"] <unpacked-structured-type>
        # 6.4.3.1 <unpacked-structured-type> ::= <array-type> | <record-type> | <set-type> | <file-type>
        #
        # This function returns the type.  If a <new-type> is created, then the <new-type> will be
        # added to the symbol table.  The name of the new type will be in the optionaltypename field.
        # If a <new-type> is created and the typename is blank, then the type name will be created
        # anonymously.  See page 69 of Cooper for discussion of anonymous types.

        if self.next_three_tokens_contain_subrange():
            return self.parse_subrangetype(parent_ast, optionaltypeidentifiertok)
        elif self.tokenstream.peektokentype() == TokenType.LPAREN:
            return self.parse_enumeratedtype(parent_ast, optionaltypeidentifiertok)
        elif self.tokenstream.peektokentype() in (TokenType.PACKED, TokenType.ARRAY, TokenType.RECORD, TokenType.SET,
                                                  TokenType.FILE):
            return self.parse_structuredtype(parent_ast, optionaltypeidentifiertok)
        else:
            existingtype = self.parse_typeidentifier(parent_ast)
            if optionaltypeidentifiertok is not None:
                # if we have an existing type, we don't need to create a symbol for an anonymous type.  But if we
                # were given a new type name, then we do need to create a symbol for it, as the statement
                # we are parsing is a type with an alias.

                newtype = deepcopy(existingtype)
                newtype.identifier = optionaltypeidentifiertok.value
                newtype.denoter = existingtype

                parent_ast.symboltable.add(newtype)
                return newtype
            else:
                return existingtype

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

        if self.tokenstream.peektokentype() == TokenType.VAR:
            assert isinstance(parent_ast.symboltable, SymbolTable),\
                "Parser.parse_variabledeclarationpart: missing symboltable"
            self.getexpectedtoken(TokenType.VAR)
            done = False
            while not done:
                identifier_list = self.parse_identifierlist()
                self.getexpectedtoken(TokenType.COLON)
                symboltype = self.parse_typedenoter(parent_ast)
                self.getexpectedtoken(TokenType.SEMICOLON)
                for identifier_token in identifier_list:
                    do_not_add = False

                    # A bit hacky, but if we are declaring a variable and we are in the outermost scope
                    # (which is only location where ProgramParameterSymbols can live) then instead of
                    # creating a new symbol, we update the existing with the correct type.  Note that
                    # error messages on duplicate symbols are handled in SymbolTable.add() so we do not
                    # need to raise any errors here if the symbol exists and is not a ProgramParameterSymbol.
                    if parent_ast.symboltable.exists(identifier_token.value):
                        tmpsym = parent_ast.symboltable.fetch(identifier_token.value)
                        if isinstance(tmpsym, ProgramParameterSymbol):
                            if not isinstance(symboltype, pascaltypes.FileType):
                                errstr = "Variable '{}' is declared as a program parameter, must be File or Text type"
                                errstr = errstr.format(identifier_token.value)
                                errstr = compiler_errstr(errstr, identifier_token)
                                raise ParseException(errstr)
                            else:
                                do_not_add = True
                                tmpsym.pascaltype = symboltype

                    if not do_not_add:
                        parent_ast.symboltable.add(VariableSymbol(identifier_token.value,
                                                                  identifier_token.location, symboltype))
                if self.tokenstream.peektokentype() != TokenType.IDENTIFIER:
                    done = True

    def parse_formalparameterlist(self, paramlist, parent_ast):
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
            symboltype = self.parse_typeidentifier(parent_ast)
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
                self.parse_formalparameterlist(ast_procfunc.paramlist, ast_procfunc)

            if tok_procfunc.tokentype == TokenType.FUNCTION:
                if self.tokenstream.peektokentype() != TokenType.COLON:
                    # see if the next token is a return type
                    tmp_symboltype = None
                    tmp_token = self.tokenstream.peektoken()
                    try:
                        tmp_symboltype = self.parse_typeidentifier(ast_procfunc)
                    except ParseException:
                        pass  # errors are ok here.

                    if tmp_symboltype is None:
                        errstr = compiler_errstr("Function {} missing return type".format(tok_procfuncname.value),
                                                 tok_procfunc)
                    else:
                        errstr = compiler_errstr("Expected ':' but saw '{}'".format(tmp_token.value), tmp_token)
                    raise ParseException(errstr)
                self.getexpectedtoken(TokenType.COLON)
                resulttype = self.parse_typeidentifier(ast_procfunc)
                # 6.6.2 - functions can only return simple types or pointers
                if not (isinstance(resulttype, pascaltypes.SimpleType) or
                        isinstance(resulttype, pascaltypes.PointerType)):
                    errstr = "Function {} has invalid return type: {}".format(tok_procfuncname.value,
                                                                                    str(resulttype),)
                    raise ParseException(compiler_errstr(errstr, tok_procfunc))
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

    def insert_ast_between(self, parent_ast, child_ast, expected_tokentype):
        # Start: the parent of child_ast is parent_ast
        # End: A new AST is created with parent = parent_ast, and child_ast as a child.
        #      child_ast's parent is reset to point to this new AST that is created.
        #      A reference to the new AST is returned

        assert isinstance(parent_ast, AST)
        assert isinstance(child_ast, AST)
        assert child_ast.parent == parent_ast
        assert isinstance(expected_tokentype, TokenType)

        ret = AST(self.getexpectedtoken(expected_tokentype), parent_ast)
        ret.children.append(child_ast)
        child_ast.parent = ret
        return ret

    def parse_variableaccess(self, parent_ast):
        # 6.5.1 <variable-access> ::= <entire-variable> | <component-variable> | <identified-variable>
        #                             | <buffer-variable>
        # 6.5.2 <entire-variable> ::= <variable-identifier>
        # 6.5.2 <variable-identifier> ::= <identifier>
        # 6.5.3.1 <component-variable> ::= <indexed-variable> | <field-designator>
        # 6.5.3.2 <indexed-variable> ::= <array-variable> "[" <index-expression> {"," <index-expression>} "]"
        # 6.5.3.2 <array-variable> ::= <variable-access>
        #       Note the recursive definition here.  The two below notations are equivalent:
        #       a[i][j]
        #       a[i,j]
        # 6.5.3.2 <index-expression> ::= <expression>
        # 6.5.3.3 <field-designator> ::= <record-variable> "." <field-specifier> | <field-designator-identifier>
        # 6.5.3.3 <field-specifier> ::= <field-identifier>
        # 6.5.3.3 <field-identifier> ::= <identifier>
        # 6.8.3.10 <field-deisgnator-identifier> ::= <identifier>
        # 6.5.4 <identified-variable> ::= <pointer-variable> "^"
        # 6.5.4 <pointer-variable> ::= <variable-access>
        # 6.5.5 <buffer-variable> ::= <file-variable> "^"
        # 6.5.5 <file-variable> ::= <variable-access>
        #
        # NOTE: if we see a function without an argument list, or a reference to a constant it will come here
        # and work fine, because we build the AST the same way for all those cases.  Same as if we are seeing
        # the lval of the assignment statement to set the return value for a function.  It might be cleaner
        # to explicitly handle those elsewhere but for now since the AST ends up the same, it's fine.
        assert self.tokenstream.peektokentype() == TokenType.IDENTIFIER

        ident_token = self.tokenstream.eattoken()
        sym = parent_ast.nearest_symboldefinition(ident_token.value)
        if isinstance(sym, ProgramParameterSymbol):
            # special case for files that are declared as Program Parameters.
            return AST(ident_token, parent_ast)
        assert isinstance(sym, VariableSymbol), "non-variable access: {}".format(sym.name)

        # if the identifier is an array, we could see one of a few valid things. Assume the array variable
        # is named myarr and has 2 dimensions.  We could see myarr by itself - meaning it's being passed into a
        # function/proc or being assigned to another variable of the same type.  We could see myarr followed by a
        # left bracket.  If we see "myarr[" - we do not know if we have the shorthand myarr[i,j] or the longer
        # myarr[i][j].  Since the contents of what is in the brackets couldbe arbitrarily long (unlimited
        # dimensions or even a single dimension with an arbitrarily complex expression) we can't easily look
        # ahead to see which form it is.  Additionally, since the definition of <array-variable> is
        # <variable-access> - we don't know until we see the second left bracket in "myarr[i][j]" that we
        # should call parse_variableaccess() recursively.  As such, we are not going to use a recursive
        # definition.  Remember also, depending on the types, this is valid syntax:
        #
        # myarr[2,3].foobar.x[7][(x+2*9+i)].fizbuz[-apple]^
        #
        # so we are going to just parse a token at a time until we lookahead and see something that would
        # cause the variable access to end, and we will iterate and create the ASTs as if we had called it
        # recursively.  This involves resetting the parents of the AST's as we go.

        mainloopdone = False
        ret = AST(ident_token, parent_ast)
        while not mainloopdone:
            nexttok = self.tokenstream.peektoken()
            if nexttok.tokentype == TokenType.POINTER:
                ret = self.insert_ast_between(parent_ast, ret, TokenType.POINTER)
                mainloopdone = True
            elif nexttok.tokentype == TokenType.PERIOD:
                ret = self.insert_ast_between(parent_ast, ret, TokenType.PERIOD)
                ret.children.append(AST(self.getexpectedtoken(TokenType.IDENTIFIER), ret))
            elif nexttok.tokentype == TokenType.LBRACKET:
                arrayloopdone = False
                ret = self.insert_ast_between(parent_ast, ret, TokenType.LBRACKET)
                while not arrayloopdone:
                    ret.children.append(self.parse_expression(ret))
                    nexttok = self.tokenstream.peektoken()
                    if nexttok.tokentype == TokenType.RBRACKET:
                        self.getexpectedtoken(TokenType.RBRACKET)
                        arrayloopdone = True
                    elif nexttok.tokentype == TokenType.COMMA:
                        ret = self.insert_ast_between(parent_ast, ret, TokenType.COMMA)
                        # change the tokentype to left bracket, because a[i,j] is shorthand for a[i][j]
                        ret.token.tokentype = TokenType.LBRACKET
                        # and now we go back to the arrayloop, parsing the expression
                    else:
                        raise ParseException(compiler_errstr("Invalid Token: '{}'".format(nexttok.value), nexttok))
            else:
                mainloopdone = True

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
                self.literaltable.add(RealLiteral(realtok.value, realtok.location))
                ret = AST(realtok, parent_ast)
            elif self.tokenstream.peektokentype() in (TokenType.UNSIGNED_INT, TokenType.TRUE,
                                                      TokenType.MAXINT, TokenType.FALSE):
                ret = AST(self.tokenstream.eattoken(), parent_ast)
            elif self.tokenstream.peektokentype() == TokenType.CHARSTRING:
                tok_charstr = self.getexpectedtoken(TokenType.CHARSTRING)
                # a string of length one is a character; a string of any other length is a string literal
                if len(tok_charstr.value) != 1:
                    # literalTable.add() allows adding duplicates
                    self.literaltable.add(StringLiteral(tok_charstr.value, tok_charstr.location))
                ret = AST(tok_charstr, parent_ast)
            elif self.tokenstream.peektokentype() == TokenType.NOT:
                nottok = self.getexpectedtoken(TokenType.NOT)
                ret = AST(nottok, parent_ast)
                ret.children.append(self.parse_factor(ret))
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
                nexttok = self.tokenstream.peektoken()
                sym = parent_ast.nearest_symboldefinition(nexttok.value)
                if sym is None:
                    raise ParseException(compiler_errstr("Undefined Identifier: '{}'".format(nexttok.value), nexttok))
                elif isinstance(sym, pascaltypes.EnumeratedTypeValue) or isinstance(sym, ConstantSymbol):
                    return AST(self.getexpectedtoken(TokenType.IDENTIFIER), parent_ast)
                elif isinstance(sym, ActivationSymbol) or isinstance(sym, FunctionResultVariableSymbol):
                    ret = AST(self.getexpectedtoken(TokenType.IDENTIFIER), parent_ast)
                    if self.tokenstream.peektokentype() == TokenType.LPAREN:
                        # we know it's supposed to be a function-designator.  But, it could be a
                        # procedure by mistake, which would be a compile error.  If it's a FunctionResultVariableSymbol
                        # it would be a recursive call, which is fine, but the nearest_symboldefinition would be
                        # the FunctionResultVariableSymbol not the ActivationSymbol, and that's by design.  Hence
                        # testing for isinstance(ActivationSymbol) in the next line before testing to see if it is
                        # a procedure call.
                        if isinstance(sym, ActivationSymbol) and sym.returntype is None:
                            if parent_ast.token.tokentype == TokenType.ASSIGNMENT:
                                errstr = "Procedure {} cannot be used as right value to assignment"
                                errstr = errstr.format(nexttok.value)
                            elif parent_ast.token.tokentype in (TokenType.TO, TokenType.DOWNTO):
                                errstr = "Procedure {} cannot be used as the final value of a 'for' statement"
                                errstr = errstr.format(nexttok.value)
                            else:
                                errstr = "Procedure {} cannot be used as parameter to {}()"
                                errstr = errstr.format(nexttok.value, parent_ast.token.value)
                            raise ParseException(compiler_errstr(errstr, ret.token))
                        self.parse_actualparameterlist(ret)
                else:
                    return self.parse_variableaccess(parent_ast)
            else:
                errtok = self.tokenstream.eattoken()
                raise ParseException(compiler_errstr("Invalid <unsigned-constant> '{}'".format(errtok.value), errtok))
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
            # now let's see if we can collapse this down.
            if ret.children[1].token.tokentype == TokenType.UNSIGNED_INT:
                ret = ret.children[1]
                # if we just update ret.token, that is actually a reference to the original token
                # in the tokenstream, which causes comments to get messed up.
                newtok = Token(TokenType.SIGNED_INT, ret.token.location, str(-1*int(ret.token.value)))
                ret.token = newtok
            elif ret.children[1].token.tokentype == TokenType.UNSIGNED_REAL:
                ret = ret.children[1]
                newtok = Token(TokenType.SIGNED_REAL, ret.token.location, str(-1.0 * float(ret.token.value)))
                # TODO - we have an extra literal here because we added the unsigned literal previously
                # do not want to remove the unsigned literal because what if we are using that literal
                self.literaltable.add(RealLiteral(newtok.value, newtok.location))
                ret.token = newtok
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

    def parse_file_procedure(self, parent_ast):
        assert self.tokenstream.peektokentype() in (TokenType.REWRITE, TokenType.RESET, TokenType.PUT, TokenType.GET), \
            "Parser.parse_file_procedure called and rewrite, reset, put, get not next token."
        self.tokenstream.setstartpos()
        ret = AST(self.tokenstream.eattoken(), parent_ast)
        self.parse_actualparameterlist(ret)
        self.tokenstream.setendpos()
        ret.comment = "Call procedure: {}".format(self.tokenstream.printstarttoend())
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
        if self.tokenstream.peektokentype() == TokenType.LPAREN:
            self.getexpectedtoken(TokenType.LPAREN)
            if self.tokenstream.peektokentype() == TokenType.OUTPUT:
                ret.children.append(AST(self.getexpectedtoken(TokenType.OUTPUT), ret))
                self.getexpectedtoken(TokenType.COMMA)

            # TODO - this is a temporary error check
            if not parent_ast.nearest_symboltable().existsanywhere("output"):
                errstr = "{}() called without 'output' defined".format(ret.token.value)
                raise ParseException(compiler_errstr(errstr, ret.token))

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

        # TODO - this may fall apart with procedures declared inside procedures:
        #
        # Procedure outer(...);
        #   var a:integer;
        #   Procedure inner(var a:char);
        #       a := 'x';
        #
        # The logic below will find the var a in outer, not the a that is a parameter to inner.

        assert self.tokenstream.peektokentype() == TokenType.IDENTIFIER
        assert parent_ast is not None

        ident_token = self.tokenstream.peektoken()

        # validate that we are assigning to a valid identifier - either a symbol or a parameter
        symtab = parent_ast.nearest_symboltable()
        if not symtab.existsanywhere(ident_token.value):
            tmp_ast = parent_ast
            tmp_paramlist = tmp_ast.paramlist
            while tmp_paramlist is None:
                assert isinstance(tmp_ast, AST)
                if tmp_ast.parent is None:
                    # we made it to the top of the AST without finding a param list.
                    errstr = "Undefined Identifier: {}".format(ident_token.value)
                    raise ParseException(compiler_errstr(errstr, ident_token))
                tmp_ast = tmp_ast.parent
                tmp_paramlist = tmp_ast.paramlist
            assert isinstance(tmp_paramlist, ParameterList)
            param = tmp_paramlist.fetch(ident_token.value)
            if param is None:
                raise ParseException(compiler_errstr("Undefined Identifier: {}".format(ident_token.value), ident_token))
            else:
                assert isinstance(param, Parameter)
        else:
            sym = symtab.fetch(ident_token.value)
            assert isinstance(sym, VariableSymbol)

        # Two possible designs considered here.  First, having ret have some token that represents
        # the variable-identifier and that it is being assigned to, and then have one child which
        # is the expression, or the one that I'm going with here, which is to have ret explicitly
        # be the assign operation with first child the variable being assigned and second child
        # being the expression.  I don't know that either is better but this seemed cleaner
        # because it put all the tokens in the AST and did not require creation of a new tokentype
        # like I did in first compiler.

        # I haven't seen the real assignment token yet, so I will create the AST with a placeholder
        ret = AST(Token(TokenType.ASSIGNMENT, None, ":="), parent_ast)
        self.tokenstream.setstartpos()
        ret.children.append(self.parse_variableaccess(ret))
        # Now assign the real token to ret
        if self.tokenstream.peektokentype() == TokenType.EQUALS:
            # TODO - is this a warning or an error?
            # TODO - name the variable instead of generic "Variable access"
            errstr = "Variable access followed by '=', was assignment intended?"
            errstr = compiler_errstr(errstr, self.tokenstream.eattoken())
            raise ParseException(errstr)

        ret.token = self.getexpectedtoken(TokenType.ASSIGNMENT)
        ret.children.append(self.parse_expression(ret))
        self.tokenstream.setendpos()
        ret.comment = self.tokenstream.printstarttoend()
        return ret

    def parse_gotostatement(self, parent_ast):
        assert parent_ast is not None
        assert self.tokenstream.peektokentype() == TokenType.GOTO, "Parser_parse_gotostatement called without goto"
        raise ParseException(compiler_errstr("goto not handled at this time", self.tokenstream.eattoken()))

    def parse_actualparameterlist(self, parent_ast):
        # 6.7.3 - <actual-parameter-list> ::= "(" <actual-parameter> {"," <actual-parameter>} ")"
        # 6.7.3 - <actual-parameter> ::= <expression> | <variable-access> | <procedure-identifier>
        #                                   | <function-identifier>
        # 6.6.1 - <procedure-identifier> ::= <identifier>
        # 6.6.2 - <function-identifier> ::= <identifier>

        # This function appends each parameter to the parent_ast as a child.

        # The <procedure-identifier> and <function-identifier> are for passing in procedures and functions
        # as parameters.  We do not support that yet.  Passing the value of a function in as a parameter
        # would come from the <factor> which in turn comes from the <expression>.  Similarly, while
        # <variable-access> is allowed here, it is also allowed in the <factor>, so it too will come
        # from the expression.

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
        self.tokenstream.setstartpos()
        curtok = self.getexpectedtoken(TokenType.IDENTIFIER)
        ret = AST(curtok, parent_ast)
        nexttok = self.tokenstream.peektoken()
        if nexttok.tokentype == TokenType.LPAREN:
            self.parse_actualparameterlist(ret)
        elif nexttok.tokentype == TokenType.ASSIGNMENT:
            errstr = compiler_errstr("Cannot assign to Procedure name '{}'".format(curtok.value), nexttok)
            raise ParseException(errstr)
        self.tokenstream.setendpos()
        ret.comment = "Call procedure: {}".format(self.tokenstream.printstarttoend())
        return ret

    def parse_simplestatement(self, parent_ast):
        # 6.8.2.1 - <simple-statement> ::= <empty-statement> | <assignment-statement> | <procedure-statement>
        #                                   | <goto-statement>
        # 6.8.2.3 - <procedure-statement> ::= procedure-identifier ([<actual-parameter-list>] | <read-parameter_list>
        #                                            | <readln-parameter-list> | <write-parameter-list>
        #                                            | <writeln-parameter-list>)
        # 6.6.1 - <procedure-identifier> ::= <identifier>
        # 6.8.2.2 - <assignment-statement> ::= (<variable-access>|<function-identifier>) ":=" <expression>

        assert parent_ast is not None

        next_tokentype = self.tokenstream.peektokentype()

        if next_tokentype in (TokenType.WRITE, TokenType.WRITELN):
            return self.parse_writeandwriteln(parent_ast)
        elif next_tokentype in (TokenType.REWRITE, TokenType.RESET, TokenType.PUT, TokenType.GET):
            return self.parse_file_procedure(parent_ast)
        elif next_tokentype == TokenType.GOTO:
            return self.parse_gotostatement(parent_ast)
        elif next_tokentype == TokenType.IDENTIFIER:
            next_tokenname = self.tokenstream.peektoken().value
            tmpsym = parent_ast.nearest_symboldefinition(next_tokenname)
            if tmpsym is None:
                raise ParseException(compiler_errstr("Identifier undefined '{}'".format(self.tokenstream.peektoken().value), self.tokenstream.peektoken()))
            elif isinstance(tmpsym, ActivationSymbol):
                if tmpsym.returntype is not None:
                    tmptok = self.tokenstream.eattoken()
                    errstr = "Cannot invoke function without assigning its return value: '{}'".format(tmptok.value)
                    raise ParseException(compiler_errstr(errstr, tmptok))
                return self.parse_procedurestatement(parent_ast)
            elif isinstance(tmpsym, VariableSymbol):
                return self.parse_assignmentstatement(parent_ast)
            elif isinstance(tmpsym, ConstantSymbol):
                tmptok = self.tokenstream.eattoken()
                errstr = "Cannot assign to constant '{}'".format(next_tokenname)
                raise ParseException(compiler_errstr(errstr, tmptok))
            else:
                tok = self.tokenstream.eattoken()
                errstr = compiler_errstr("Identifier '{}' seen, unclear how to parse".format(tok.value), tok)
                raise ParseException(errstr)
        else:
            tmptok = self.tokenstream.eattoken()
            raise ParseException(compiler_errstr("Invalid Token: '{}'".format(tmptok.value), tmptok))

    def parse_ifstatement(self, parent_ast):
        # 6.8.3.4 <if-statement> ::= "if" <Boolean-expression> "then" <statement> [else-part]
        # 6.8.3.4 <else-part> ::= "else" <statement>
        # 6.7.2.3 <Boolean-expression> ::= <expression>
        assert self.tokenstream.peektokentype() == TokenType.IF, \
            "Parser.parse_ifstatement called and 'if' not next token. {}".format(self.tokenstream.peektokentype())

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
        ret = AST(self.getexpectedtoken(TokenType.REPEAT), parent_ast)
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

    def parse_forstatement(self, parent_ast):
        # 6.8.3.9 <for-statement> := "for" <control-variable> ":=" <initial-value> ("to"|"downto") <final-value>
        #                               "do" <statement>
        # 6.8.3.9 <control-variable> := <entire-variable>
        # 6.5.2 <entire-variable> := <variable-identifier>
        # 6.5.2 <variable-identifier> := <identifier>
        # 6.8.3.9 <initial-value> := <expression>
        # 6.8.3.9 <final-value> := <expression>
        #
        assert self.tokenstream.peektokentype() == TokenType.FOR, \
            "Parser.parse_forstatement called and 'for' not next token."

        self.tokenstream.setstartpos()
        ret = AST(self.getexpectedtoken(TokenType.FOR), parent_ast)
        nexttwo = self.tokenstream.peekmultitokentype(2)
        if nexttwo[0] != TokenType.IDENTIFIER:
            tmptok = self.tokenstream.eattoken()
            errstr = compiler_errstr("Identifier expected following 'for' statement, instead saw: '{}'".format(tmptok.value),
                                     tmptok)
            raise ParseException(errstr)
        if nexttwo[1] != TokenType.ASSIGNMENT:
            self.tokenstream.eattoken()  # eat the identifier
            self.getexpectedtoken(TokenType.ASSIGNMENT)  # will generate the exception and exit
            assert False  # pragma: no cover (only here so reader can see we exited at the line immediately above)

        assignast = self.parse_assignmentstatement(ret)
        ret.children.append(assignast)

        if self.tokenstream.peektokentype() not in (TokenType.TO, TokenType.DOWNTO):
            tmptok = self.tokenstream.eattoken()
            errstr = compiler_errstr("'to' or 'downto' expected, instead saw: '{}'".format(tmptok.value), tmptok)
            raise ParseException(errstr)

        self.tokenstream.setstartpos()
        todowntoast = AST(self.tokenstream.eattoken(), ret)
        self.tokenstream.setendpos()
        todowntoast.comment = self.tokenstream.printstarttoend()
        finalvalueast = self.parse_expression(todowntoast)
        todowntoast.children.append(finalvalueast)
        ret.children.append(todowntoast)
        self.getexpectedtoken(TokenType.DO)
        self.tokenstream.setendpos()
        ret.comment = self.tokenstream.printstarttoend()
        ret.children.append(self.parse_statement(ret))

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
            ret = self.parse_forstatement(parent_ast)
        return ret

    def parse_structuredstatement(self, parent_ast):
        # 6.8.3.1 - <structured-statement> ::= <compound-statement> | <conditional-statement>
        #                                       | <repetitive-statement> | <with-statement>

        # with-statement is not currently supported.
        # while-statement and repeat-statement are the repetitive statements supported.

        if self.tokenstream.peektokentype() == TokenType.BEGIN:
            return self.parse_compoundstatement(parent_ast)
        elif self.tokenstream.peektokentype() in (TokenType.WHILE, TokenType.REPEAT, TokenType.FOR):
            return self.parse_repetitivestatement(parent_ast)
        else:
            return self.parse_conditionalstatement(parent_ast)

    def parse_statement(self, parent_ast):
        # 6.8.1 - <statement> ::= [<label>:] (<simple-statement> | <structured-statement>)
        # labels are not yet supported
        assert parent_ast is not None

        next_tokentype = self.tokenstream.peektokentype()
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
                # TODO - for both Semicolon expected errors, need to show the previous line too.
                raise ParseException(compiler_errstr ("Semicolon expected", self.tokenstream.peekprevioustoken()))

    def parse_compoundstatement(self, parent_ast):
        # 6.8.3.2 - <compound-statement> ::= "begin" <statement-sequence> "end"
        # 6.8.3.1 - <statement-sequence> ::= <statement> [ ";" <statement> ]
        # 6.8.1 - <statement> ::= [<label>:] (<simple-statement> | <structured-statement>)
        # 6.8.2.1 - <simple-statement> ::= <empty-statement> | <assignment-statement> | <procedure-statement>
        #                                   | <goto-statement>
        # This function returns an AST node using the BEGIN as the token, and with one child for each
        # statement.
        ret = AST(self.getexpectedtoken(TokenType.BEGIN), parent_ast)
        # If we see the END right after the BEGIN we have an <empty-statement> so we do nothing
        # else we parse the statement sequence
        if self.tokenstream.peektokentype() != TokenType.END:
            self.parse_statementsequence(TokenType.END, ret)

        # The expected token here is an END.  However, if the END does not appear, we will try to keep parsing
        # so that other parse errors could be displayed later.  It is frustrating for an end user to have
        # compilation die on the first error.
        endtok = self.tokenstream.eattoken()
        if endtok.tokentype != TokenType.END:
            errstr = compiler_errstr("Expected 'end' but saw '{0}'".format(str(endtok.value)), endtok)
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

        # parse_typedefinitionpart updates the symbol table, does not return anything to be added to the AST
        self.parse_typedefinitionpart(parent_ast)

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
        # currently we do not do anything with the program name, so no need to assign getexpectedtoken to a value
        self.getexpectedtoken(TokenType.IDENTIFIER)
        if self.tokenstream.peektokentype() == TokenType.LPAREN:
            position = 1
            self.getexpectedtoken(TokenType.LPAREN)
            while self.tokenstream.peektokentype() != TokenType.RPAREN:
                tok = self.tokenstream.eattoken()
                if tok.tokentype == TokenType.INPUT:
                    # TODO - this adding the ProgramParameterSymbol separate from the type identifier into symboltable
                    # is not consistent with how we add other types like integer, real, etc.  Probably need to add
                    # "text" when we add the simple types, and then have tftd.denoter = the text base type?  Not sure.
                    tftd = pascaltypes.TextFileType("input")
                    ret.symboltable.add(ProgramParameterSymbol("input", tok.location, tftd, None))
                elif tok.tokentype == TokenType.OUTPUT:
                    tftd = pascaltypes.TextFileType("output")
                    ret.symboltable.add(ProgramParameterSymbol("output", tok.location, tftd, None))
                elif tok.tokentype == TokenType.IDENTIFIER:
                    # when we run into the definition of this, we will change the componenttype if it is not text
                    ftd = pascaltypes.FileType(tok.value, pascaltypes.CharacterType())
                    ret.symboltable.add(ProgramParameterSymbol(tok.value, tok.location, ftd, position))
                    position += 1
                else:
                    raise ParseException(compiler_errstr("Invalid program parameter '{}'".format(tok.value), tok))
                if self.tokenstream.peektokentype() != TokenType.RPAREN:
                    self.getexpectedtoken(TokenType.COMMA)
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
