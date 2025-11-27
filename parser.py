from lexer import TokenType, Token, TokenStream, LexerException, REQUIRED_IDENTIFIER_TO_TOKEN_TYPE_LOOKUP
from symboltable import StringLiteral, LiteralTable, SymbolTable, VariableSymbol, ParameterList, \
    ActivationSymbol, FunctionResultVariableSymbol, Parameter, SymbolException, ConstantSymbol, RealLiteral, \
    CharacterLiteral, ProgramParameterSymbol
from compiler_error import compiler_error_str, compiler_fail_str
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


def is_relational_operator(token_type):
    # 6.7.2.1 <relational-operator> ::= "=" | "<>" | "<" | ">" | "<=" | ">=" | "in"
    assert isinstance(token_type, TokenType)
    if token_type in (TokenType.EQUALS, TokenType.NOTEQUAL, TokenType.LESS, TokenType.GREATER,
                      TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL, TokenType.IN):
        return True
    else:
        return False


def is_multiplying_operator(token_type):
    # 6.7.2.1 <multiplying-operator> ::= "*" | "/" | "div" | "mod" | "and"
    assert isinstance(token_type, TokenType)
    if token_type in (TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.INTEGER_DIV, TokenType.MOD, TokenType.AND):
        return True
    else:
        return False


def is_adding_operator(token_type):
    # 6.7.2.1 <adding-operator> ::= "+" | "-" | "or"
    assert isinstance(token_type, TokenType)
    if token_type in (TokenType.PLUS, TokenType.MINUS, TokenType.OR):
        return True
    else:
        return False


def is_iso_required_function(token_type):
    # 6.6.6 in the ISO Standard lists required functions.
    assert isinstance(token_type, TokenType)
    if token_type in (TokenType.ABS, TokenType.SQR, TokenType.SIN, TokenType.COS, TokenType.EXP,
                      TokenType.LN, TokenType.SQRT, TokenType.ARCTAN, TokenType.TRUNC,
                      TokenType.ROUND, TokenType.ORD, TokenType.CHR, TokenType.SUCC, TokenType.PRED,
                      TokenType.ODD, TokenType.EOF, TokenType.EOLN):
        return True
    else:
        return False


def starts_structured_statement(token_type):
    # 6.8.3.1 - <structured-statement> ::= <compound-statement> | <conditional-statement>
    #                                       | <repetitive-statement> | <with-statement>

    # compound statement starts with "begin"
    # conditional statements start with "if" or "case"
    # repetitive statements start with "repeat," "while,"or "for"
    # with statements start with "with"

    if token_type in (TokenType.BEGIN, TokenType.IF, TokenType.CASE, TokenType.REPEAT, TokenType.WHILE,
                      TokenType.FOR, TokenType.WITH):
        return True
    else:
        return False


class ParseException(Exception):
    pass


class AST:
    def __init__(self, token, parent, comment=""):
        assert isinstance(token, Token), "AST.__init__: AST requires a token"
        self.token = token
        self.comment = comment  # will get put on the line emitted in the assembly code if populated.
        self.children = []
        if parent is not None:
            assert isinstance(parent, AST), "AST.__init__:Parent of AST must be an AST"
        self.parent = parent  # pointer back to the parent node in the AST
        self.symbol_table = None  # will only be defined for Procedure, Function, and Program tokens
        self.parameter_list = None  # will only be defined for Procedure and Function tokens


    def init_symbol_table(self):
        self.symbol_table = SymbolTable()

        if self.parent is None:
            # root of the tree gets the type identifiers for the required types
            self.symbol_table.add_simple_types()
        else:
            # every other symbol table has to have a pointer to its parent, and there must be a parent
            # since the root has a symbol_table and this is not the root.
            ptr = self.parent
            while ptr.symbol_table is None:
                ptr = ptr.parent
                # the root of the AST has a symbol_table for globals, so since this node is not the root
                # it should never get to None.
                assert ptr is not None, "AST.init_symbol_table: No symbol_table in AST ancestry"
            assert isinstance(ptr.symbol_table, SymbolTable)
            self.symbol_table.parent = ptr.symbol_table

    def init_parameter_list(self):
        self.parameter_list = ParameterList()

    def rpn_print(self, level=0):  # pragma: no cover
        # used only for debugging
        return_string = ""
        if self.comment != "":
            return_string = "{};{}\n".format((level * " "), self.comment)

        return_string += "{}{}\n".format((level * " "), str(self.token))

        for child in self.children:
            return_string += child.rpn_print(level + 1)
        return return_string

    def nearest_symbol_table(self):
        ptr = self
        while ptr.symbol_table is None:
            ptr = ptr.parent
            # the root of the AST has a symbol_table for globals, so ptr should never get to None
            assert ptr is not None, "AST.nearest_symbol_table: No symbol_table in AST ancestry"
        assert isinstance(ptr.symbol_table, SymbolTable)
        return ptr.symbol_table

    def nearest_symbol_definition(self, symbol_name):
        # returns the nearest symbol with a given identifier, None if the symbol is not defined.
        # checks the local symbol table, then the local parameter list, then goes to the parent ast
        # and repeats, until symbol is found, or the top of the tree is reached.

        ptr = self
        ret = None
        while ptr is not None and ret is None:
            if ptr.symbol_table is not None and ptr.symbol_table.exists(symbol_name):
                ret = ptr.symbol_table.fetch(symbol_name)  # errors if not found, hence testing exists()
            elif ptr.parameter_list is not None:
                parameter = ptr.parameter_list.fetch(symbol_name)  # returns None if not found
                if parameter is not None:
                    ret = parameter.symbol
            ptr = ptr.parent
        return ret

    def nearest_param_list(self):
        # returns None if no parameter_list above this node in the tree, meaning the statement is outside
        # a procedure or function.
        # TODO - where this is used, we will have a problem with nested procs/funcs.
        ptr = self
        while ptr is not None and ptr.parameter_list is None:
            ptr = ptr.parent
        if ptr is None:
            return None
        else:
            return ptr.parameter_list

    def dump_symbol_tables(self):  # pragma: no cover
        # used only for debugging
        for child in self.children:
            child.dump_symbol_tables()
        if self.symbol_table is not None:
            print(str(self.symbol_table))
            print("*****")


# TODO - add a class for a parse warning/parse error - likely the same thing, a string, a location, maybe a level?
class Parser:
    def __init__(self, tokenstream):
        assert isinstance(tokenstream, TokenStream), "Parser.__init__: Can only parse TokenStreams"
        self.tokenstream = tokenstream
        self.AST = None
        self.parse_error_list = []
        self.parse_warning_list = []
        self.literal_table = LiteralTable()
        self.anonymous_type_counter = 0

    def get_expected_token(self, token_type):
        assert isinstance(token_type, TokenType), compiler_fail_str(
            "Parser.get_expected_token: Expected Token must be a token not {}".format(type(token_type)))

        token = self.tokenstream.peek_token()
        if token.token_type != token_type:
            if token_type == TokenType.SEMICOLON:
                # TODO - insert a semicolon into the stream and allow parsing to continue
                error_str = compiler_error_str("Semicolon expected", self.tokenstream.peek_previous_token())
            else:
                error_str = compiler_error_str("Expected '{0}' but saw '{1}'".format(str(token_type),
                                                                                     str(token.value)), token)
            raise ParseException(error_str)

        return_token = self.tokenstream.eat_token()
        assert isinstance(return_token, Token), compiler_fail_str(
            "Parser.get_expected_token: attempt to return non-Token {}".format(type(return_token)))
        return return_token

    def override_next_identifier_to_required_identifier_if_needed(self, ast):
        assert self.tokenstream.peek_token_type() == TokenType.IDENTIFIER
        symbol = ast.nearest_symbol_definition(self.tokenstream.peek_token().value)
        if symbol is None:
            if self.tokenstream.peek_token().value.lower() in REQUIRED_IDENTIFIER_TO_TOKEN_TYPE_LOOKUP.keys():
                self.tokenstream.override_next_identifier_to_required_identifier(
                    REQUIRED_IDENTIFIER_TO_TOKEN_TYPE_LOOKUP[self.tokenstream.peek_token().value.lower()])

    def parse_label_declaration_part(self, parent_ast):
        assert isinstance(parent_ast, AST)
        return_list = []
        if self.tokenstream.peek_token_type() == TokenType.LABEL:
            raise ParseException(compiler_error_str("labels not handled at this time", self.tokenstream.eat_token()))
        return return_list

    def parse_constant(self, parent_ast, optional_constant_id=""):
        # returns a tuple (type of the constant, value of the constant)
        # value of the constant will be a string
        # optional_constant_id is if you are using this to parse a constant definition, it enables us to catch a
        # self-referencing constant definition.
        #
        # 6.3 <constant> ::= [sign] (<unsigned-number> | <constant-identifier>) | <character-string>
        # 6.1.5 <sign> ::= "+" | "-"
        # 6.3 <constant-identifier> ::= <identifier>
        # 6.1.7 <character-string> ::= "'" <string-element> {<string-element>} "'"
        #
        # p.65 of [Cooper] states that if a constant has a sign then the next token must be
        # a real, an integer, or a real/integer constant.  That can't be captured in the BNF.

        # this is to avoid PyCharm flagging that return_token_type_value_tuple may not be assigned before it's used
        return_token_type_value_tuple = None

        if self.tokenstream.peek_token_type() == TokenType.MINUS:
            self.get_expected_token(TokenType.MINUS)
            is_negative = True
            saw_sign = True
        else:
            if self.tokenstream.peek_token_type() == TokenType.PLUS:
                saw_sign = True
                self.get_expected_token(TokenType.PLUS)
            else:
                saw_sign = False
            is_negative = False

        if self.tokenstream.peek_token_type() == TokenType.IDENTIFIER:
            self.override_next_identifier_to_required_identifier_if_needed(parent_ast)

        if self.tokenstream.peek_token_type() == TokenType.UNSIGNED_REAL:
            real_token = self.get_expected_token(TokenType.UNSIGNED_REAL)
            if is_negative:
                token_value = "-" + real_token.value
            else:
                token_value = real_token.value
            self.literal_table.add(RealLiteral(token_value, real_token.location))
            return_token_type_value_tuple = pascaltypes.RealType(), token_value
        elif self.tokenstream.peek_token_type() == TokenType.UNSIGNED_INT:
            int_token = self.get_expected_token(TokenType.UNSIGNED_INT)
            if is_negative:
                token_value = "-" + int_token.value
            else:
                token_value = int_token.value
            return_token_type_value_tuple = pascaltypes.IntegerType(), token_value
        elif self.tokenstream.peek_token_type() == TokenType.MAXINT:
            self.get_expected_token(TokenType.MAXINT)
            if is_negative:
                return_token_type_value_tuple = pascaltypes.IntegerType(), pascaltypes.NEGATIVE_MAXINT_AS_STRING
            else:
                return_token_type_value_tuple = pascaltypes.IntegerType(), pascaltypes.MAXINT_AS_STRING
        elif self.tokenstream.peek_token_type() in (TokenType.TRUE, TokenType.FALSE):
            bool_token = self.tokenstream.eat_token()
            if saw_sign:
                error_str = compiler_error_str("Cannot have a sign before a Boolean constant", bool_token)
                raise ParseException(error_str)
            return_token_type_value_tuple = pascaltypes.BooleanType(), bool_token.value
        elif self.tokenstream.peek_token_type() == TokenType.CHARSTRING:
            character_string_token = self.get_expected_token(TokenType.CHARSTRING)
            if saw_sign:
                error_str = compiler_error_str("Cannot have a sign before a string constant", character_string_token)
                raise ParseException(error_str)
            if len(character_string_token.value) == 1:
                self.literal_table.add(CharacterLiteral(character_string_token.value, character_string_token.location))
                return_token_type_value_tuple = pascaltypes.CharacterType(), character_string_token.value
            else:
                self.literal_table.add(StringLiteral(character_string_token.value, character_string_token.location))
                return_token_type_value_tuple = pascaltypes.StringLiteralType(), character_string_token.value
        elif self.tokenstream.peek_token_type() == TokenType.IDENTIFIER:
            identifier_token = self.get_expected_token(TokenType.IDENTIFIER)
            if not parent_ast.symbol_table.exists_anywhere(identifier_token.value):
                if identifier_token.value == optional_constant_id:
                    error_str = compiler_error_str(
                        "Self-referencing constant definition '{}'".format(identifier_token.value),
                        identifier_token)
                else:
                    error_str = compiler_error_str("Undefined Identifier: '{}'".format(identifier_token.value),
                                                   identifier_token)
                raise ParseException(error_str)
            symbol = parent_ast.symbol_table.fetch(identifier_token.value)
            if not isinstance(symbol, ConstantSymbol) and not isinstance(symbol, pascaltypes.EnumeratedTypeValue):
                if optional_constant_id != "":
                    error_str = "Constant '{}' must be defined as a literal or another constant, cannot use '{}'"
                    error_str = error_str.format(optional_constant_id, identifier_token.value)
                else:
                    error_str = "Constant expected, must be literal or another constant, cannot use '{}'"
                    error_str = error_str.format(identifier_token.value)
                error_str = compiler_error_str(error_str, identifier_token)
                raise ParseException(error_str)
            if saw_sign:
                invalid_sign = False
                if isinstance(symbol, pascaltypes.EnumeratedTypeValue):
                    invalid_sign = True
                else:
                    assert isinstance(symbol, ConstantSymbol)

                    if isinstance(symbol.pascal_type, pascaltypes.RealType) or \
                            isinstance(symbol.pascal_type, pascaltypes.IntegerType):
                        if is_negative:
                            if symbol.value[0] == "-":
                                token_value = symbol.value[1:]  # remove the negative
                            else:
                                token_value = "-" + symbol.value
                            # If we define a constant as negative another constant, we need to ensure the
                            # literal value is in the literals table if it's a real constant.
                            # LiteralTable.add() allows adding duplicates and filters them out.
                            if isinstance(symbol.pascal_type, pascaltypes.RealType):
                                self.literal_table.add(RealLiteral(token_value, identifier_token.location))
                                return_token_type_value_tuple = symbol.pascal_type, token_value
                            else:
                                return_token_type_value_tuple = symbol.pascal_type, token_value
                        else:
                            token_value = symbol.value
                            return_token_type_value_tuple = symbol.pascal_type, token_value
                    else:
                        invalid_sign = True

                if invalid_sign:
                    error_str = "Constant '{}' is not numeric."
                    if optional_constant_id != "":
                        error_str += " Cannot define constant '{}' ".format(optional_constant_id)
                    else:
                        error_str += " Cannot define constant "
                    error_str += "by putting a sign before a non-numeric constant."
                    error_str = error_str.format(identifier_token.value)
                    raise ParseException(compiler_error_str(error_str, identifier_token))
            elif isinstance(symbol, pascaltypes.EnumeratedTypeValue):
                enumerated_type = \
                    parent_ast.symbol_table.fetch_original_symbol_table_and_type(symbol.type_identifier)[1]
                return_token_type_value_tuple = enumerated_type, identifier_token.value
            else:
                assert isinstance(symbol, ConstantSymbol)
                token_value = symbol.value
                return_token_type_value_tuple = symbol.pascal_type, token_value
        else:
            next_token = self.tokenstream.eat_token()
            error_str = "Unexpected token {}".format(str(next_token.value))
            raise ParseException(compiler_error_str(error_str, next_token))

        # None isn't valid, but we assigned to None to avoid return_token_type_value_tuple not assigned warning below
        assert return_token_type_value_tuple is not None
        return return_token_type_value_tuple

    def parse_constant_definition_part(self, parent_ast):
        # 6.2.1 <constant-definition-part> ::= [ "const" <constant-definition> ";" {<constant-definition> ";"} ]
        # 6.3 <constant-definition> ::= <identifier> "=" <constant>

        if self.tokenstream.peek_token_type() == TokenType.CONST:
            assert isinstance(parent_ast.symbol_table, SymbolTable), \
                "Parser.parse_constant_definition_part: missing symbol_table"
            self.get_expected_token(TokenType.CONST)
            done = False
            while not done:
                constant_id = self.get_expected_token(TokenType.IDENTIFIER)
                self.get_expected_token(TokenType.EQUALS)
                constant_type, constant_value = self.parse_constant(parent_ast, constant_id.value)
                if isinstance(constant_type, pascaltypes.RealType):
                    new_symbol_type = pascaltypes.RealType()
                elif isinstance(constant_type, pascaltypes.IntegerType):
                    new_symbol_type = pascaltypes.IntegerType()
                elif isinstance(constant_type, pascaltypes.BooleanType):
                    new_symbol_type = pascaltypes.BooleanType()
                elif isinstance(constant_type, pascaltypes.CharacterType):
                    new_symbol_type = pascaltypes.CharacterType()
                elif isinstance(constant_type, pascaltypes.StringLiteralType):
                    new_symbol_type = pascaltypes.StringLiteralType()
                else:
                    new_symbol_type = constant_type
                parent_ast.symbol_table.add(
                    ConstantSymbol(constant_id.value, constant_id.location, new_symbol_type, constant_value))
                try:
                    self.get_expected_token(TokenType.SEMICOLON)
                except ParseException as e:
                    if self.tokenstream.peek_token_type() in (TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY,
                                                              TokenType.DIVIDE, TokenType.LEFT_PAREN,
                                                              TokenType.RIGHT_PAREN,
                                                              TokenType.INTEGER_DIV, TokenType.MOD):
                        # if the token is related to expressions, we will do a specific error for that.
                        error_str = compiler_error_str(
                            "Semicolon expected, cannot define a constant in terms of an expression",
                            self.tokenstream.peek_token())
                        raise ParseException(error_str)
                    else:
                        raise e
                if self.tokenstream.peek_token_type() != TokenType.IDENTIFIER:
                    done = True

        return None

    def next_three_tokens_contain_subrange(self):
        # 6.4.2.4 <subrange-type> ::= <constant> ".." <constant>
        # So we have a subrange if the token two ahead contains a subrange token, or the token 3 ahead
        # contains a subrange token.  Hard to write in a single line, legibly, so I broke it out.
        next3 = self.tokenstream.peek_multi_token_type(3)
        if next3[1] == TokenType.SUBRANGE or next3[2] == TokenType.SUBRANGE:
            return True
        else:
            return False

    def parse_type_definition_part(self, parent_ast):
        # 6.2.1 <type-definition-part> ::= ["type" <type-definition> ";" {<type-definition> ";"} ]
        # 6.4.1 <type-definition> ::= <identifier> "=" <type-denoter>

        if self.tokenstream.peek_token_type() == TokenType.TYPE:
            assert isinstance(parent_ast.symbol_table, SymbolTable), \
                "Parser.parse_type_definition_part: missing symbol_table"

            self.get_expected_token(TokenType.TYPE)
            done = False
            while not done:
                identifier = self.get_expected_token(TokenType.IDENTIFIER)
                self.get_expected_token(TokenType.EQUALS)
                self.parse_type_denoter(parent_ast, identifier)
                self.get_expected_token(TokenType.SEMICOLON)
                if self.tokenstream.peek_token_type() != TokenType.IDENTIFIER:
                    done = True

    def parse_type_identifier(self, parent_ast):
        # 6.4.1 <type-identifier> ::= <identifier>
        #   The valid type-identifiers are the simple types (integer, char, boolean, real), file types and identifiers
        #   that have already been defined for other types.
        #
        # Returns a type

        if self.tokenstream.peek_token_type() == TokenType.IDENTIFIER:
            self.override_next_identifier_to_required_identifier_if_needed(parent_ast)

        type_token = self.tokenstream.eat_token()
        if type_token.token_type not in (TokenType.INTEGER, TokenType.REAL, TokenType.BOOLEAN,
                                         TokenType.CHAR, TokenType.TEXT, TokenType.IDENTIFIER):
            error_str = "Invalid type identifier '{}'".format(type_token.value)
            raise ParseException(compiler_error_str(error_str, type_token))

        if type_token.token_type == TokenType.IDENTIFIER:
            symboltype = parent_ast.symbol_table.fetch(type_token.value)
        else:
            symboltype = parent_ast.symbol_table.fetch(str(type_token.token_type))
        if not isinstance(symboltype, pascaltypes.BaseType):
            raise ParseException(
                compiler_error_str("Invalid type identifier '{}'".format(type_token.value), type_token))
        return symboltype

    def generate_anonymous_type_identifier(self):
        # begins with an underscore so can never clash with a valid pascal identifier.
        ret = "_anonymous_{}".format(str(self.anonymous_type_counter))
        self.anonymous_type_counter += 1
        return ret

    def parse_subrange_type(self, parent_ast, optional_type_identifier_token=None):
        # 6.4.2.4 <subrange-type> ::= <constant> ".." <constant>
        # 6.3 <constant> ::= [sign](<unsigned-number> | <constant-identifier>) | <character-string>
        #   (character-string is not valid for subrange types, however)
        #
        # Note that the text of 6.4.2.4 states that "Both constants shall be of the same ordinal type,"
        # even though <unsigned-number> allows for integers or reals.
        #
        # This function returns the type.  If a <new-type> is created, then the <new-type> will be
        # added to the symbol table.  The name of the new type will be in the optional_type_identifier field.
        # If a <new-type> is created and the typename is blank, then the type name will be created
        # anonymously.  See page 69 of Cooper for discussion of anonymous types.

        assert self.next_three_tokens_contain_subrange()

        optional_type_identifier = ""
        if optional_type_identifier_token is not None:
            optional_type_identifier = optional_type_identifier_token.value

        next_token = self.tokenstream.peek_token()  # used for error messages
        constant1_type, constant1_value = self.parse_constant(parent_ast)
        self.get_expected_token(TokenType.SUBRANGE)
        constant2_type, constant2_value = self.parse_constant(parent_ast)
        if not parent_ast.symbol_table.are_same_type(constant1_type.identifier, constant2_type.identifier):
            error_str = "Both elements of subrange type {} must be same type."
            error_str += "'{}' is type {} and '{}' is type {}"
            # optional_type_identifier may be blank here, and that's ok for the error message, rather than
            # plugging in an anonymous type
            error_str = error_str.format(optional_type_identifier, constant1_value, constant1_type.identifier,
                                         constant2_value, constant2_type.identifier)
            raise ParseException(compiler_error_str(error_str, next_token))

        if not isinstance(constant1_type, pascaltypes.OrdinalType) or not isinstance(constant2_type,
                                                                                     pascaltypes.OrdinalType):
            error_str = "Both elements of subrange type {} must be ordinal type."
            error_str += " Types {} and {} are used"
            error_str = error_str.format(optional_type_identifier, constant1_type.identifier, constant2_type.identifier)
            raise ParseException(compiler_error_str(error_str, next_token))

        if optional_type_identifier == "":
            type_identifier = self.generate_anonymous_type_identifier()
        else:
            type_identifier = optional_type_identifier

        try:
            ret = pascaltypes.SubrangeType(type_identifier, constant1_type, constant1_value, constant2_value)
        except pascaltypes.PascalTypeException as e:
            raise ParseException(compiler_error_str(e, next_token))

        parent_ast.symbol_table.add(ret)
        return ret

    def parse_enumerated_type(self, parent_ast, optional_type_name_token=None):
        # 6.4.2.3 <enumerated-type> ::= "(" <identifier-list> ")"
        # 6.4.2.3 <identifier-list> ::= <identifier> {"," <identifier>}
        #
        # This function returns the type.  If a <new-type> is created, then the <new-type> will be
        # added to the symbol table.  The name of the new type will be in the optional_type_name field.
        # If a <new-type> is created and the typename is blank, then the type name will be created
        # anonymously.  See page 69 of Cooper for discussion of anonymous types.

        self.get_expected_token(TokenType.LEFT_PAREN)

        if optional_type_name_token is None:
            typename = self.generate_anonymous_type_identifier()
        else:
            typename = optional_type_name_token.value

        identifier_list = self.parse_identifier_list()
        enumerated_type_value_list = []
        for identifier_token in identifier_list:
            new_enumerated_type_value = pascaltypes.EnumeratedTypeValue(identifier_token.value, typename,
                                                                        len(enumerated_type_value_list))
            enumerated_type_value_list.append(new_enumerated_type_value)
            try:
                parent_ast.symbol_table.add(new_enumerated_type_value)
            except SymbolException:
                error_str = compiler_error_str("Identifier redefined: '{}'".format(identifier_token.value),
                                               identifier_token)
                raise ParseException(error_str)

        try:
            return_type = pascaltypes.EnumeratedType(typename, enumerated_type_value_list)
        except pascaltypes.PascalTypeException as e:
            raise ParseException(compiler_error_str(e, optional_type_name_token))
        self.get_expected_token(TokenType.RIGHT_PAREN)

        parent_ast.symbol_table.add(return_type)
        return return_type

    def parse_index_type_list(self, parent_ast):
        # 6.4.3.2 <array-type> ::= "array" "[" <index-type> {"," <index-type>} "]" "of" <component-type>
        # 6.4.3.2 <index-type> ::= <ordinal-type>
        # 6.4.2.1 <ordinal-type> ::= <new-ordinal-type> | <ordinal-type-identifier>
        # 6.4.2.1 <new-ordinal-type> ::= <enumerated-type> | <subrange-type>
        #
        # returns a list of types
        return_type_list = []
        done = False

        while not done:
            token = self.tokenstream.peek_token()  # used for error messages
            new_type = self.parse_type_denoter(parent_ast)
            if not isinstance(new_type, pascaltypes.OrdinalType):
                raise ParseException(
                    compiler_error_str("Invalid type for array index '{}'".format(token.value), token))
            return_type_list.append(new_type)
            if self.tokenstream.peek_token_type() == TokenType.COMMA:
                self.get_expected_token(TokenType.COMMA)
            else:
                done = True
        return return_type_list

    def parse_structured_type(self, parent_ast, optional_type_identifier_token=None):
        # 6.4.3.1 <new-structured-type> ::= ["packed"] <unpacked-structured-type>
        # 6.4.3.1 <unpacked-structured-type> ::= <array-type> | <record-type> | <set-type> | <file-type>
        # 6.4.3.2 <array-type> ::= "array" "[" <index-type> {"," <index-type>} "]" "of" <component-type>
        # 6.4.3.2 <index-type> ::= <ordinal-type>
        # 6.4.2.1 <ordinal-type> ::= <new-ordinal-type> | <ordinal-type-identifier>
        # 6.4.2.1 <new-ordinal-type> ::= <enumerated-type> | <subrange-type>
        # 6.4.3.2 <component-type> ::= <type-denoter>
        #
        # This function returns the type.  If a <new-type> is created, then the <new-type> will be
        # added to the symbol table.  The name of the new type will be in the optional_type_identifier field.
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

        optional_type_identifier = ""
        if optional_type_identifier_token is not None:
            optional_type_identifier = optional_type_identifier_token.value

        if self.tokenstream.peek_token_type() == TokenType.PACKED:
            self.get_expected_token(TokenType.PACKED)
            is_packed = True
        else:
            is_packed = False

        if self.tokenstream.peek_token_type() == TokenType.ARRAY:

            self.get_expected_token(TokenType.ARRAY)
            self.get_expected_token(TokenType.LEFT_BRACKET)
            index_type_list = self.parse_index_type_list(parent_ast)
            self.get_expected_token(TokenType.RIGHT_BRACKET)
            self.get_expected_token(TokenType.OF)
            component_type = self.parse_type_denoter(parent_ast)

            # iterate through the indextype list backwards.

            new_type = component_type
            for i in range(-1, (-1 * len(index_type_list)) - 1, -1):
                indextype = index_type_list[i]
                # the typename passed into this function goes to the outermost array definition.
                # If it is shorthand for multiple arrays, then the inner array definitions are all
                # anonymously named.
                if i == (-1 * len(index_type_list)) and optional_type_identifier != "":
                    type_identifier = optional_type_identifier
                else:
                    type_identifier = self.generate_anonymous_type_identifier()

                # the new_type variable will be overwritten every type through the loop, so only
                # the final one processed will be returned
                new_type = pascaltypes.ArrayType(type_identifier, indextype, new_type, is_packed)
                parent_ast.symbol_table.add(new_type)
            return new_type

        else:
            tok = self.tokenstream.eat_token()
            raise ParseException(compiler_error_str("Invalid Structured Type {}".format(tok.value), tok))

    def parse_type_denoter(self, parent_ast, optional_type_identifier_token=None):
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
        # added to the symbol table.  The name of the new type will come from the optional_type_identifier_token.
        # If a <new-type> is created and the typename is blank, then the type name will be created
        # anonymously.  See page 69 of Cooper for discussion of anonymous types.

        if self.next_three_tokens_contain_subrange():
            return self.parse_subrange_type(parent_ast, optional_type_identifier_token)
        elif self.tokenstream.peek_token_type() == TokenType.LEFT_PAREN:
            return self.parse_enumerated_type(parent_ast, optional_type_identifier_token)
        elif self.tokenstream.peek_token_type() in (TokenType.PACKED, TokenType.ARRAY, TokenType.RECORD, TokenType.SET,
                                                    TokenType.FILE):
            return self.parse_structured_type(parent_ast, optional_type_identifier_token)
        else:
            existing_type = self.parse_type_identifier(parent_ast)
            if optional_type_identifier_token is not None:
                # if we have an existing type, we don't need to create a symbol for an anonymous type.  But if we
                # were given a new type name, then we do need to create a symbol for it, as the statement
                # we are parsing is a type with an alias.

                new_type = deepcopy(existing_type)
                new_type.identifier = optional_type_identifier_token.value
                new_type.denoter = existing_type

                parent_ast.symbol_table.add(new_type)
                return new_type
            else:
                return existing_type

    def parse_identifier_list(self):
        # 6.4.2.3 <identifier-list> ::= <identifier> { "," <identifier> }
        # 6.1.3 <identifier> ::= <letter> {<letter> | <digit>}
        #
        # returns a python list of one or more identifier tokens
        ret = [self.get_expected_token(TokenType.IDENTIFIER)]
        while self.tokenstream.peek_token_type() == TokenType.COMMA:
            self.get_expected_token(TokenType.COMMA)
            ret.append(self.get_expected_token(TokenType.IDENTIFIER))
        return ret

    def parse_variable_declaration_part(self, parent_ast):
        # 6.2.1 <variable-declaration-part> ::= [ "var" <variable-declaration> ";" {<variable-declaration> ";"} ]
        # 6.5.1 <variable-declaration> ::= <identifier-list> ":" <type-denoter>
        # 6.4.2.3 <identifier-list> ::= <identifier> { "," <identifier> }
        # 6.1.3 <identifier> ::= <letter> {<letter> | <digit>}

        if self.tokenstream.peek_token_type() == TokenType.VAR:
            assert isinstance(parent_ast.symbol_table, SymbolTable), \
                "Parser.parse_variable_declaration_part: missing symbol_table"
            self.get_expected_token(TokenType.VAR)
            done = False
            while not done:
                identifier_list = self.parse_identifier_list()
                self.get_expected_token(TokenType.COLON)
                symbol_type = self.parse_type_denoter(parent_ast)
                self.get_expected_token(TokenType.SEMICOLON)
                for identifier_token in identifier_list:
                    do_not_add = False

                    # A bit hacky, but if we are declaring a variable, and we are in the outermost scope
                    # (which is only location where ProgramParameterSymbols can live) then instead of
                    # creating a new symbol, we update the existing with the correct type.  Note that
                    # error messages on duplicate symbols are handled in SymbolTable.add() so we do not
                    # need to raise any errors here if the symbol exists and is not a ProgramParameterSymbol.
                    if parent_ast.symbol_table.exists(identifier_token.value):
                        symbol = parent_ast.symbol_table.fetch(identifier_token.value)
                        if isinstance(symbol, ProgramParameterSymbol):
                            if not isinstance(symbol_type, pascaltypes.FileType):
                                error_str = \
                                    "Variable '{}' is declared as a program parameter, must be File or Text type"
                                error_str = error_str.format(identifier_token.value)
                                error_str = compiler_error_str(error_str, identifier_token)
                                raise ParseException(error_str)
                            else:
                                do_not_add = True
                                symbol.pascal_type = symbol_type

                    if not do_not_add:
                        parent_ast.symbol_table.add(
                            VariableSymbol(identifier_token.value, identifier_token.location, symbol_type))
                if self.tokenstream.peek_token_type() != TokenType.IDENTIFIER:
                    done = True

    def parse_formal_parameter_list(self, parameter_list, parent_ast):
        # 6.6.3.1 - <formal-parameter-list> ::= "(" <formal-parameter-section> {";" <formal-parameter-section>} ")"
        # 6.6.3.1 - <formal-parameter-section> ::= <value-parameter-specification> | <variable-parameter-specification>
        #                                           | <procedural-parameter-specification>
        #                                           | <functional-parameter-specification>
        # 6.6.3.1 - <value-parameter-specification> ::= <identifier-list> ":" <type-identifier>
        # 6.6.3.1 - <variable-parameter-specification> ::= "var" <identifier-list> ":" <type-identifier>
        # The procedural/functional parameter specification are for passing procedures or functions as parameters,
        # which we do not support now.
        assert isinstance(parameter_list, ParameterList)

        self.get_expected_token(TokenType.LEFT_PAREN)

        done = False
        while not done:
            if self.tokenstream.peek_token_type() == TokenType.VAR:
                self.get_expected_token(TokenType.VAR)
                is_by_ref = True
            else:
                is_by_ref = False
            identifier_list = self.parse_identifier_list()
            self.get_expected_token(TokenType.COLON)
            symbol_type = self.parse_type_identifier(parent_ast)
            for identifier_token in identifier_list:
                variable_symbol = VariableSymbol(identifier_token.value, identifier_token.location, symbol_type)
                variable_symbol.is_by_ref = is_by_ref
                parameter_list.add(Parameter(variable_symbol, is_by_ref))
            if self.tokenstream.peek_token_type() == TokenType.SEMICOLON:
                self.get_expected_token(TokenType.SEMICOLON)
            else:
                done = True
        self.get_expected_token(TokenType.RIGHT_PAREN)

    def parse_procedure_and_function_declaration_part(self, parent_ast):
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

        return_ast_list = []
        while self.tokenstream.peek_token_type() in [TokenType.PROCEDURE, TokenType.FUNCTION]:
            procedure_or_function_token = self.tokenstream.eat_token()
            assert isinstance(procedure_or_function_token, Token)
            procedure_or_function_ast = AST(procedure_or_function_token, parent_ast)
            procedure_or_function_ast.init_symbol_table()
            procedure_or_function_ast.init_parameter_list()
            activation_symbol_name_token = self.get_expected_token(TokenType.IDENTIFIER)
            procedure_or_function_ast.children.append(AST(activation_symbol_name_token, procedure_or_function_ast))
            assert isinstance(activation_symbol_name_token, Token)
            if self.tokenstream.peek_token_type() == TokenType.LEFT_PAREN:
                self.parse_formal_parameter_list(procedure_or_function_ast.parameter_list, procedure_or_function_ast)

            if procedure_or_function_token.token_type == TokenType.FUNCTION:
                if self.tokenstream.peek_token_type() != TokenType.COLON:
                    # see if the next token is a return type
                    symbol_type = None
                    next_token = self.tokenstream.peek_token()
                    try:
                        symbol_type = self.parse_type_identifier(procedure_or_function_ast)
                    except ParseException:
                        pass  # errors are ok here.

                    if symbol_type is None:
                        error_str = compiler_error_str(
                            "Function {} missing return type".format(activation_symbol_name_token.value),
                            procedure_or_function_token)
                    else:
                        error_str = compiler_error_str("Expected ':' but saw '{}'".format(next_token.value), next_token)
                    raise ParseException(error_str)
                self.get_expected_token(TokenType.COLON)
                result_type = self.parse_type_identifier(procedure_or_function_ast)
                # 6.6.2 - functions can only return simple types or pointers
                if not (isinstance(result_type, pascaltypes.SimpleType) or
                        isinstance(result_type, pascaltypes.PointerType)):
                    error_str = "Function {} has invalid return type: {}".format(activation_symbol_name_token.value,
                                                                                 str(result_type))
                    raise ParseException(compiler_error_str(error_str, procedure_or_function_token))
                procedure_or_function_ast.symbol_table.add(
                    FunctionResultVariableSymbol(activation_symbol_name_token.value,
                                                 activation_symbol_name_token.location, result_type))
                activation_type = pascaltypes.FunctionType()
            else:
                result_type = None
                activation_type = pascaltypes.ProcedureType()

            # Procedures and Functions can only be declared in Program scope, or in the scope of other procedures
            # or functions.  So the parent of the procedure or function here has to have a symbol table.
            parent_ast.symbol_table.add(
                ActivationSymbol(activation_symbol_name_token.value, activation_symbol_name_token.location,
                                 activation_type,
                                 procedure_or_function_ast.parameter_list, result_type))

            self.get_expected_token(TokenType.SEMICOLON)
            procedure_or_function_ast.children.extend(self.parse_block(procedure_or_function_ast))
            self.get_expected_token(TokenType.SEMICOLON)
            return_ast_list.append(procedure_or_function_ast)
        return return_ast_list

    def insert_ast_between(self, parent_ast, child_ast, expected_token_type):
        # Start: the parent of child_ast is parent_ast
        # End: A new AST is created with parent = parent_ast, and child_ast as a child.
        #      child_ast's parent is reset to point to this new AST that is created.
        #      A reference to the new AST is returned

        assert isinstance(parent_ast, AST)
        assert isinstance(child_ast, AST)
        assert child_ast.parent == parent_ast
        assert isinstance(expected_token_type, TokenType)

        ret = AST(self.get_expected_token(expected_token_type), parent_ast)
        ret.children.append(child_ast)
        child_ast.parent = ret
        return ret

    def parse_variable_access(self, parent_ast):
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
        # 6.8.3.10 <field-designator-identifier> ::= <identifier>
        # 6.5.4 <identified-variable> ::= <pointer-variable> "^"
        # 6.5.4 <pointer-variable> ::= <variable-access>
        # 6.5.5 <buffer-variable> ::= <file-variable> "^"
        # 6.5.5 <file-variable> ::= <variable-access>
        #
        # NOTE: if we see a function without an argument list, or a reference to a constant it will come here
        # and work fine, because we build the AST the same way for all those cases.  Same as if we are seeing
        # the left value of the assignment statement to set the return value for a function.  It might be cleaner
        # to explicitly handle those elsewhere but for now since the AST ends up the same, it's fine.
        assert self.tokenstream.peek_token_type() == TokenType.IDENTIFIER

        identifier_token = self.tokenstream.eat_token()
        symbol = parent_ast.nearest_symbol_definition(identifier_token.value)
        if isinstance(symbol, ProgramParameterSymbol):
            # special case for files that are declared as Program Parameters.
            return AST(identifier_token, parent_ast)
        if not isinstance(symbol, VariableSymbol):
            raise ParseException(compiler_error_str("Access of non-variable: {}".format(symbol.name), identifier_token))

        # If the identifier is an array, we could see one of a few valid things. Assume the array variable
        # is named array1 and has 2 dimensions.  We could see array1 by itself - meaning it's being passed into a
        # function/proc or being assigned to another variable of the same type.  We could see array1 followed by a
        # left bracket.  If we see "array1[" - we do not know if we have the shorthand array1[i,j] or the longer
        # array1[i][j].  Since the contents of what is in the brackets could be arbitrarily long (unlimited
        # dimensions or even a single dimension with an arbitrarily complex expression) we can't easily look
        # ahead to see which form it is.  Additionally, since the definition of <array-variable> is
        # <variable-access> - we don't know until we see the second left bracket in "array1[i][j]" that we
        # should call parse_variable_access() recursively.  As such, we are not going to use a recursive
        # definition.  Remember also, depending on the types, this is valid syntax:
        #
        # array1[2,3].foobar.x[7][(x+2*9+i)].buzz[-apple]^
        #
        # So we are going to just parse a token at a time until we look ahead and see something that would
        # cause the variable access to end, and we will iterate and create the ASTs as if we had called it
        # recursively.  This involves resetting the parents of the AST's as we go.

        main_loop_done = False
        return_ast = AST(identifier_token, parent_ast)
        while not main_loop_done:
            next_token = self.tokenstream.peek_token()
            if next_token.token_type == TokenType.POINTER:
                return_ast = self.insert_ast_between(parent_ast, return_ast, TokenType.POINTER)
                main_loop_done = True
            elif next_token.token_type == TokenType.PERIOD:
                return_ast = self.insert_ast_between(parent_ast, return_ast, TokenType.PERIOD)
                return_ast.children.append(AST(self.get_expected_token(TokenType.IDENTIFIER), return_ast))
            elif next_token.token_type == TokenType.LEFT_BRACKET:
                array_loop_done = False
                return_ast = self.insert_ast_between(parent_ast, return_ast, TokenType.LEFT_BRACKET)
                while not array_loop_done:
                    return_ast.children.append(self.parse_expression(return_ast))
                    next_token = self.tokenstream.peek_token()
                    if next_token.token_type == TokenType.RIGHT_BRACKET:
                        self.get_expected_token(TokenType.RIGHT_BRACKET)
                        array_loop_done = True
                    elif next_token.token_type == TokenType.COMMA:
                        return_ast = self.insert_ast_between(parent_ast, return_ast, TokenType.COMMA)
                        # change the token type to left bracket, because a[i,j] is shorthand for a[i][j]
                        return_ast.token.token_type = TokenType.LEFT_BRACKET
                        # and now we go back to the array loop, parsing the expression
                    else:
                        raise ParseException(
                            compiler_error_str("Invalid Token: '{}'".format(next_token.value), next_token))
            else:
                main_loop_done = True

        return return_ast

    def parse_factor(self, parent_ast):
        # 6.7.1 <factor> ::= <variable-access> | <unsigned-constant> | <function-designator> |
        #                    <set-constructor> | "(" <expression> ")" | "not" <factor>
        # 6.7.1 <unsigned-constant> ::= <unsigned-number> | <character-string> | <constant-identifier> | "nil"
        # 6.1.7 <character-string> ::= "'" <string-element> {<string-element>} "'"
        # 6.3 <constant-identifier> ::= <identifier>
        # 6.7.3 <function-designator> ::= <function-identifier> [<actual-parameter-list>]
        # 6.6.2 <function-identifier> ::= <identifier>
        # 6.7.3 <actual-parameter-list> ::= "(" <actual-parameter> {"," <actual-parameter>} ")"

        # If the next token is an identifier, but it is not a defined symbol, it may be a required identifier.
        # If so, change the token type to the system token so we process correctly.
        if self.tokenstream.peek_token_type() == TokenType.IDENTIFIER:
            self.override_next_identifier_to_required_identifier_if_needed(parent_ast)

        if self.tokenstream.peek_token_type() == TokenType.LEFT_PAREN:
            self.get_expected_token(TokenType.LEFT_PAREN)
            return_ast = self.parse_expression(parent_ast)
            self.get_expected_token(TokenType.RIGHT_PAREN)
        else:
            if self.tokenstream.peek_token_type() == TokenType.UNSIGNED_REAL:
                real_token = self.get_expected_token(TokenType.UNSIGNED_REAL)
                self.literal_table.add(RealLiteral(real_token.value, real_token.location))
                return_ast = AST(real_token, parent_ast)
            elif self.tokenstream.peek_token_type() in (TokenType.UNSIGNED_INT, TokenType.TRUE,
                                                        TokenType.MAXINT, TokenType.FALSE):
                return_ast = AST(self.tokenstream.eat_token(), parent_ast)
            elif self.tokenstream.peek_token_type() == TokenType.CHARSTRING:
                character_string_token = self.get_expected_token(TokenType.CHARSTRING)
                # a string of length one is a character; a string of any other length is a string literal
                if len(character_string_token.value) != 1:
                    # literalTable.add() allows adding duplicates
                    self.literal_table.add(StringLiteral(character_string_token.value, character_string_token.location))
                return_ast = AST(character_string_token, parent_ast)
            elif self.tokenstream.peek_token_type() == TokenType.NOT:
                not_token = self.get_expected_token(TokenType.NOT)
                return_ast = AST(not_token, parent_ast)
                return_ast.children.append(self.parse_factor(return_ast))
            elif is_iso_required_function(self.tokenstream.peek_token_type()):
                # 6.6.6 in the ISO Standard lists required functions.  All required functions take one
                # argument.  Note, by parsing it this way instead of parsing out the parameter list, we will
                # compile error with a right paren is expected instead of a comma, instead of number of
                # parameters not matching the 1 that is expected.
                return_ast = AST(self.tokenstream.eat_token(), parent_ast)
                self.get_expected_token(TokenType.LEFT_PAREN)
                return_ast.children.append(self.parse_expression(return_ast))
                self.get_expected_token(TokenType.RIGHT_PAREN)
            elif self.tokenstream.peek_token_type() == TokenType.IDENTIFIER:
                next_token = self.tokenstream.peek_token()
                sym = parent_ast.nearest_symbol_definition(next_token.value)
                if sym is None:
                    raise ParseException(
                        compiler_error_str("Undefined Identifier: '{}'".format(next_token.value), next_token))
                elif isinstance(sym, pascaltypes.EnumeratedTypeValue) or isinstance(sym, ConstantSymbol):
                    return AST(self.get_expected_token(TokenType.IDENTIFIER), parent_ast)
                elif isinstance(sym, ActivationSymbol) or isinstance(sym, FunctionResultVariableSymbol):
                    return_ast = AST(self.get_expected_token(TokenType.IDENTIFIER), parent_ast)
                    if self.tokenstream.peek_token_type() == TokenType.LEFT_PAREN:
                        # we know it's supposed to be a function-designator.  But, it could be a
                        # procedure by mistake, which would be a compile error.  If it's a FunctionResultVariableSymbol
                        # it would be a recursive call, which is fine, but the nearest symbol definition would be
                        # the FunctionResultVariableSymbol not the ActivationSymbol, and that's by design.  Hence,
                        # testing for isinstance(ActivationSymbol) in the next line before testing to see if it is
                        # a procedure call.
                        if isinstance(sym, ActivationSymbol) and sym.result_type is None:
                            if parent_ast.token.token_type == TokenType.ASSIGNMENT:
                                error_str = "Procedure {} cannot be used as right value to assignment"
                                error_str = error_str.format(next_token.value)
                            elif parent_ast.token.token_type in (TokenType.TO, TokenType.DOWNTO):
                                error_str = "Procedure {} cannot be used as the final value of a 'for' statement"
                                error_str = error_str.format(next_token.value)
                            else:
                                error_str = "Procedure {} cannot be used as parameter to {}()"
                                error_str = error_str.format(next_token.value, parent_ast.token.value)
                            raise ParseException(compiler_error_str(error_str, return_ast.token))
                        self.parse_actual_parameter_list(return_ast)
                else:
                    return self.parse_variable_access(parent_ast)
            else:
                error_token = self.tokenstream.eat_token()
                error_str = compiler_error_str("Unsigned constant expected, instead saw '{}'".format(error_token.value),
                                               error_token)
                raise ParseException(error_str)
        return return_ast

    def parse_term(self, parent_ast):
        # 6.7.1 <term> ::= <factor> { <multiplying-operator> <factor> }
        # 6.7.2.1 <multiplying-operator> ::= "*" | "/" | "div" | "mod" | "and"
        return_ast = self.parse_factor(parent_ast)
        while is_multiplying_operator(self.tokenstream.peek_token_type()):
            multiplying_operator_ast = AST(self.tokenstream.eat_token(), parent_ast)
            return_ast.parent = multiplying_operator_ast
            multiplying_operator_ast.children.append(return_ast)
            multiplying_operator_ast.children.append(self.parse_factor(multiplying_operator_ast))
            return_ast = multiplying_operator_ast
        return return_ast

    def parse_simple_expression(self, parent_ast):
        # 6.7.1 <simple-expression> ::= [sign] <term> { <adding-operator> <term> }
        # 6.1.5 <sign> ::= "+" | "-"
        # 6.7.2.1 <adding-operator> ::= "+" | "-" | "or"

        if self.tokenstream.peek_token_type() == TokenType.MINUS:
            # a minus here is identical to multiplying by -1.
            minus_token = self.get_expected_token(TokenType.MINUS)
            return_ast = AST(Token(TokenType.MULTIPLY, minus_token.location, ""), parent_ast)
            return_ast.children.append(AST(Token(TokenType.SIGNED_INT, minus_token.location, "-1"), return_ast))
            return_ast.children.append(self.parse_term(return_ast))
            # now let's see if we can collapse this down.
            if return_ast.children[1].token.token_type == TokenType.UNSIGNED_INT:
                return_ast = return_ast.children[1]
                # if we just update return_ast.token, that is actually a reference to the original token
                # in the tokenstream, which causes comments to get messed up.
                new_token = Token(TokenType.SIGNED_INT, return_ast.token.location,
                                  str(-1 * int(return_ast.token.value)))
                return_ast.token = new_token
            elif return_ast.children[1].token.token_type == TokenType.UNSIGNED_REAL:
                return_ast = return_ast.children[1]
                new_token = Token(TokenType.SIGNED_REAL, return_ast.token.location,
                                  str(-1.0 * float(return_ast.token.value)))
                # TODO - we have an extra literal here because we added the unsigned literal previously
                # do not want to remove the unsigned literal because what if we are using that literal
                self.literal_table.add(RealLiteral(new_token.value, new_token.location))
                return_ast.token = new_token
        else:
            if self.tokenstream.peek_token_type() == TokenType.PLUS:
                # a plus sign here is a no-op
                self.get_expected_token(TokenType.PLUS)
            return_ast = self.parse_term(parent_ast)

        while is_adding_operator(self.tokenstream.peek_token_type()):
            adding_operator_ast = AST(self.tokenstream.eat_token(), parent_ast)
            return_ast.parent = adding_operator_ast
            adding_operator_ast.children.append(return_ast)
            adding_operator_ast.children.append(self.parse_term(adding_operator_ast))
            return_ast = adding_operator_ast

        return return_ast

    def parse_expression(self, parent_ast):
        # 6.7.1 - <expression> ::= <simple-expression> [<relational-operator> <simple-expression>]

        simple_expression_ast = self.parse_simple_expression(parent_ast)
        if is_relational_operator(self.tokenstream.peek_token_type()):
            relational_operator_ast = AST(self.tokenstream.eat_token(), parent_ast)
            simple_expression_ast.parent = relational_operator_ast
            relational_operator_ast.children.append(simple_expression_ast)
            relational_operator_ast.children.append(self.parse_simple_expression(relational_operator_ast))
            ret = relational_operator_ast
        else:
            ret = simple_expression_ast
        return ret

    def parse_file_procedure(self, parent_ast):
        assert self.tokenstream.peek_token_type() in (TokenType.REWRITE, TokenType.RESET,
                                                      TokenType.PUT, TokenType.GET), \
            "Parser.parse_file_procedure called and rewrite, reset, put, get not next token."
        self.tokenstream.set_start_print_position()
        return_ast = AST(self.tokenstream.eat_token(), parent_ast)
        self.parse_actual_parameter_list(return_ast)
        self.tokenstream.set_end_print_position()
        return_ast.comment = "Call procedure: {}".format(self.tokenstream.print_start_to_end())
        return return_ast

    def parse_write_and_writeln(self, parent_ast):
        # 6.8.2.3 - <procedure-statement> ::= procedure-identifier ([<actual-parameter-list>] | <read-parameter_list>
        #                                            | <readln-parameter-list> | <write-parameter-list>
        #                                            | <writeln-parameter-list>)
        # 6.6.1 - <procedure-identifier> ::= <identifier>
        # 6.9.3 - <write-parameter-list> ::= "(" [<file-variable> "."] <write-parameter>  {"," <write-parameter>} ")"
        # 6.9.4 - <writeln-parameter-list> ::= "(" [<file-variable> "."] <write-parameter>  {"," <write-parameter>} ")"
        # 6.9.3 - <write-parameter> ::= <expression> [":" <expression> [ ":" <expression> ] ]

        assert self.tokenstream.peek_token_type() in (TokenType.WRITE, TokenType.WRITELN), \
            "Parser.parse_write_and_writeln called and write/writeln not next token."

        self.tokenstream.set_start_print_position()

        return_ast = AST(self.tokenstream.eat_token(), parent_ast)
        if self.tokenstream.peek_token_type() == TokenType.LEFT_PAREN:
            self.get_expected_token(TokenType.LEFT_PAREN)
            if self.tokenstream.peek_token_type() == TokenType.OUTPUT:
                return_ast.children.append(AST(self.get_expected_token(TokenType.OUTPUT), return_ast))
                self.get_expected_token(TokenType.COMMA)

            # TODO - this is a temporary error check
            if not parent_ast.nearest_symbol_table().exists_anywhere("output"):
                error_str = "{}() called without 'output' defined".format(return_ast.token.value)
                raise ParseException(compiler_error_str(error_str, return_ast.token))

            done = False
            while not done:
                return_ast.children.append(self.parse_expression(return_ast))
                if self.tokenstream.peek_token_type() == TokenType.COMMA:
                    self.get_expected_token(TokenType.COMMA)
                else:
                    done = True
            self.get_expected_token(TokenType.RIGHT_PAREN)
        self.tokenstream.set_end_print_position()
        return_ast.comment = self.tokenstream.print_start_to_end()
        return return_ast

    def parse_assignment_statement(self, parent_ast):
        # 6.8.2.2 - <assignment-statement> ::= (<variable-access>|<function-identifier>) ":=" <expression>

        # TODO - this may fall apart with procedures declared inside procedures:
        #
        # Procedure outer(...);
        #   var a:integer;
        #   Procedure inner(var a:char);
        #       a := 'x';
        #
        # The logic below will find the var a in outer, not the a that is a parameter to inner.

        assert self.tokenstream.peek_token_type() == TokenType.IDENTIFIER
        assert parent_ast is not None
        ident_token = self.tokenstream.peek_token()

        # validate that we are assigning to a valid identifier - either a symbol or a parameter
        symbol_table = parent_ast.nearest_symbol_table()
        if not symbol_table.exists_anywhere(ident_token.value):
            temp_ast = parent_ast
            temp_parameter_list = temp_ast.parameter_list
            while temp_parameter_list is None:
                assert isinstance(temp_ast, AST)
                assert temp_ast.parent is not None, "Top of AST without finding parameter list"
                temp_ast = temp_ast.parent
                temp_parameter_list = temp_ast.parameter_list
            assert isinstance(temp_parameter_list, ParameterList)
            parameter = temp_parameter_list.fetch(ident_token.value)
            assert isinstance(parameter, Parameter)
        else:
            sym = symbol_table.fetch(ident_token.value)
            assert isinstance(sym, VariableSymbol)

        # Two possible designs considered here.  First, having return_ast have some token that represents
        # the variable-identifier and that it is being assigned to, and then have one child which
        # is the expression, or the one that I'm going with here, which is to have return_ast explicitly
        # be the assign operation with first child the variable being assigned and second child
        # being the expression.  I don't know that either is better but this seemed cleaner
        # because it put all the tokens in the AST and did not require creation of a new token type
        # like I did in first compiler.

        # I haven't seen the real assignment token yet, so I will create the AST with a placeholder
        return_ast = AST(Token(TokenType.ASSIGNMENT, None, ":="), parent_ast)
        self.tokenstream.set_start_print_position()
        return_ast.children.append(self.parse_variable_access(return_ast))
        # Now assign the real token to return_ast
        if self.tokenstream.peek_token_type() == TokenType.EQUALS:
            # TODO - is this a warning or an error?
            # TODO - name the variable instead of generic "Variable access"
            error_str = "Variable access followed by '=', was assignment intended?"
            error_str = compiler_error_str(error_str, self.tokenstream.eat_token())
            raise ParseException(error_str)

        return_ast.token = self.get_expected_token(TokenType.ASSIGNMENT)
        return_ast.children.append(self.parse_expression(return_ast))
        self.tokenstream.set_end_print_position()
        return_ast.comment = self.tokenstream.print_start_to_end()
        return return_ast

    def parse_goto_statement(self, parent_ast):
        assert parent_ast is not None
        assert self.tokenstream.peek_token_type() == TokenType.GOTO, "Parser.parse_goto_statement called without goto"
        raise ParseException(compiler_error_str("goto not handled at this time", self.tokenstream.eat_token()))

    def parse_actual_parameter_list(self, parent_ast):
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
        #   i:=x;   {this computes x and stores the result in "i."  This is unlike C where it would be i=x();}
        #   i:=b(x);  {this computes x, takes the result and passes it in as a parameter to b}
        #   i:=c(x);  {this passes the function x as a parameter to c}
        # end.
        #
        # You can't tell the difference between i:=b(a) and i:=c(a) without looking at the parameter lists for b and c.
        # However, the AST for both will be the same - b or c as identifiers with a single child with x as an
        # identifier.  The AST will be interpreted when generating the TAC, because at that time the parsing pass has
        # been completed and all the symbol tables will have been built and can be queried.
        assert isinstance(parent_ast, AST)

        self.get_expected_token(TokenType.LEFT_PAREN)
        done = False
        while not done:
            parent_ast.children.append(self.parse_expression(parent_ast))
            if self.tokenstream.peek_token_type() == TokenType.COMMA:
                self.get_expected_token(TokenType.COMMA)
            else:
                done = True
        self.get_expected_token(TokenType.RIGHT_PAREN)

    def parse_procedure_statement(self, parent_ast):
        # 6.8.2.3 - <procedure-statement> ::= procedure-identifier ([<actual-parameter-list>] | <read-parameter_list>
        #                                            | <readln-parameter-list> | <write-parameter-list>
        #                                            | <writeln-parameter-list>)
        # 6.6.1 - <procedure-identifier> ::= <identifier>
        assert self.tokenstream.peek_token_type() == TokenType.IDENTIFIER, \
            "Parser.parse_procedure_statement called and identifier not next token."
        self.tokenstream.set_start_print_position()
        current_token = self.get_expected_token(TokenType.IDENTIFIER)
        return_ast = AST(current_token, parent_ast)
        next_token = self.tokenstream.peek_token()
        if next_token.token_type == TokenType.LEFT_PAREN:
            self.parse_actual_parameter_list(return_ast)
        elif next_token.token_type == TokenType.ASSIGNMENT:
            error_str = compiler_error_str("Cannot assign to Procedure name '{}'".format(current_token.value),
                                           next_token)
            raise ParseException(error_str)
        self.tokenstream.set_end_print_position()
        return_ast.comment = "Call procedure: {}".format(self.tokenstream.print_start_to_end())
        return return_ast

    def parse_simple_statement(self, parent_ast):
        # 6.8.2.1 - <simple-statement> ::= <empty-statement> | <assignment-statement> | <procedure-statement>
        #                                   | <goto-statement>
        # 6.8.2.3 - <procedure-statement> ::= procedure-identifier ([<actual-parameter-list>] | <read-parameter_list>
        #                                            | <readln-parameter-list> | <write-parameter-list>
        #                                            | <writeln-parameter-list>)
        # 6.6.1 - <procedure-identifier> ::= <identifier>
        # 6.8.2.2 - <assignment-statement> ::= (<variable-access>|<function-identifier>) ":=" <expression>

        assert parent_ast is not None

        if self.tokenstream.peek_token_type() == TokenType.IDENTIFIER:
            self.override_next_identifier_to_required_identifier_if_needed(parent_ast)

        next_token_type = self.tokenstream.peek_token_type()

        if next_token_type in (TokenType.WRITE, TokenType.WRITELN):
            return self.parse_write_and_writeln(parent_ast)
        elif next_token_type in (TokenType.REWRITE, TokenType.RESET, TokenType.PUT, TokenType.GET):
            return self.parse_file_procedure(parent_ast)
        elif next_token_type == TokenType.GOTO:
            return self.parse_goto_statement(parent_ast)
        elif next_token_type == TokenType.IDENTIFIER:
            next_token_name = self.tokenstream.peek_token().value
            symbol = parent_ast.nearest_symbol_definition(next_token_name)
            if symbol is None:
                raise ParseException(
                    compiler_error_str("Identifier undefined '{}'".format(self.tokenstream.peek_token().value),
                                       self.tokenstream.peek_token()))
            elif isinstance(symbol, ActivationSymbol):
                if symbol.result_type is not None:
                    token = self.tokenstream.eat_token()
                    error_str = "Cannot invoke function without assigning its return value: '{}'".format(token.value)
                    raise ParseException(compiler_error_str(error_str, token))
                return self.parse_procedure_statement(parent_ast)
            elif isinstance(symbol, VariableSymbol):
                return self.parse_assignment_statement(parent_ast)
            elif isinstance(symbol, ConstantSymbol):
                token = self.tokenstream.eat_token()
                error_str = "Cannot assign to constant '{}'".format(next_token_name)
                raise ParseException(compiler_error_str(error_str, token))
            else:  # pragma: no cover
                token = self.tokenstream.eat_token()
                error_str = compiler_error_str("Identifier '{}' seen, unclear how to parse".format(token.value), token)
                raise ParseException(error_str)
        else:
            token = self.tokenstream.eat_token()
            raise ParseException(compiler_error_str("Invalid Token: '{}'".format(token.value), token))

    def parse_if_statement(self, parent_ast):
        # 6.8.3.4 <if-statement> ::= "if" <Boolean-expression> "then" <statement> [else-part]
        # 6.8.3.4 <else-part> ::= "else" <statement>
        # 6.7.2.3 <Boolean-expression> ::= <expression>
        assert self.tokenstream.peek_token_type() == TokenType.IF, \
            "Parser.parse_if_statement called and 'if' not next token. {}".format(self.tokenstream.peek_token_type())

        self.tokenstream.set_start_print_position()
        return_ast = AST(self.tokenstream.eat_token(), parent_ast)
        return_ast.children.append(self.parse_expression(return_ast))
        self.get_expected_token(TokenType.THEN)
        self.tokenstream.set_end_print_position()
        # this makes the comment "If <condition> Then" which is fine.
        return_ast.comment = self.tokenstream.print_start_to_end()

        return_ast.children.append(self.parse_statement(return_ast))
        if self.tokenstream.peek_token_type() == TokenType.ELSE:
            self.get_expected_token(TokenType.ELSE)
            # The comment "ELSE" is added in tac_ir.py - that is a bit hacky but it works
            # TODO - figure out if I can add a comment "ELSE" here and remove that one.
            return_ast.children.append(self.parse_statement(return_ast))
        return return_ast

    def parse_conditional_statement(self, parent_ast):
        # 6.8.3.3 - <conditional-statement> ::= <if-statement> | <case-statement>
        return self.parse_if_statement(parent_ast)

    def parse_while_statement(self, parent_ast):
        # 6.8.3.8 - <while-statement> ::= "while" <Boolean-expression> "do" <statement>
        # 6.7.2.3 - <Boolean-expression> ::= <expression>
        assert self.tokenstream.peek_token_type() == TokenType.WHILE, \
            "Parser.parse_while_statement called and 'while' not next token."

        self.tokenstream.set_start_print_position()
        return_ast = AST(self.tokenstream.eat_token(), parent_ast)
        return_ast.children.append(self.parse_expression(return_ast))
        self.get_expected_token(TokenType.DO)
        self.tokenstream.set_end_print_position()
        # this makes the comment "while <condition> do" which is fine.
        return_ast.comment = self.tokenstream.print_start_to_end()
        if self.tokenstream.peek_token_type() == TokenType.SEMICOLON:
            # Special case <empty-statement>
            no_op_token = Token(TokenType.EMPTY_TOKEN, self.tokenstream.peek_token().location, '')
            return_ast.children.append(AST(no_op_token, return_ast))
        else:
            return_ast.children.append(self.parse_statement(return_ast))
        return return_ast

    def parse_repeat_statement(self, parent_ast):
        # 6.8.3.7 - <repeat-statement> ::= "repeat" <statement-sequence> "until" <Boolean-expression>
        # 6.7.2.3 - <Boolean-expression> ::= <expression>
        assert self.tokenstream.peek_token_type() == TokenType.REPEAT, \
            "Parser.parse_repeat_statement called and 'repeat' not next token."

        self.tokenstream.set_start_print_position()
        return_ast = AST(self.get_expected_token(TokenType.REPEAT), parent_ast)
        self.tokenstream.set_end_print_position()
        repeat_comment = self.tokenstream.print_start_to_end()

        self.parse_statement_sequence(TokenType.UNTIL, return_ast)

        self.tokenstream.set_start_print_position()
        self.get_expected_token(TokenType.UNTIL)
        return_ast.children.append(self.parse_expression(return_ast))
        self.tokenstream.set_end_print_position()
        until_comment = self.tokenstream.print_start_to_end()
        # comment will be "repeat until <condition>"
        return_ast.comment = "{0} {1}".format(repeat_comment, until_comment)
        return return_ast

    def parse_for_statement(self, parent_ast):
        # 6.8.3.9 <for-statement> := "for" <control-variable> ":=" <initial-value> ("to"|"downto") <final-value>
        #                               "do" <statement>
        # 6.8.3.9 <control-variable> := <entire-variable>
        # 6.5.2 <entire-variable> := <variable-identifier>
        # 6.5.2 <variable-identifier> := <identifier>
        # 6.8.3.9 <initial-value> := <expression>
        # 6.8.3.9 <final-value> := <expression>
        #
        assert self.tokenstream.peek_token_type() == TokenType.FOR, \
            "Parser.parse_for_statement called and 'for' not next token."

        self.tokenstream.set_start_print_position()
        return_ast = AST(self.get_expected_token(TokenType.FOR), parent_ast)
        next_two_tokens = self.tokenstream.peek_multi_token_type(2)
        if next_two_tokens[0] != TokenType.IDENTIFIER:
            token = self.tokenstream.eat_token()
            error_str = compiler_error_str(
                "Identifier expected following 'for' statement, instead saw: '{}'".format(token.value), token)
            raise ParseException(error_str)
        if next_two_tokens[1] != TokenType.ASSIGNMENT:
            self.tokenstream.eat_token()  # eat the identifier
            self.get_expected_token(TokenType.ASSIGNMENT)  # will generate the exception and exit
            assert False  # pragma: no cover (only here so reader can see we exited at the line immediately above)

        assignment_ast = self.parse_assignment_statement(return_ast)
        return_ast.children.append(assignment_ast)

        if self.tokenstream.peek_token_type() not in (TokenType.TO, TokenType.DOWNTO):
            token = self.tokenstream.eat_token()
            error_str = compiler_error_str("'to' or 'downto' expected, instead saw: '{}'".format(token.value), token)
            raise ParseException(error_str)

        self.tokenstream.set_start_print_position()
        to_downto_ast = AST(self.tokenstream.eat_token(), return_ast)
        self.tokenstream.set_end_print_position()
        to_downto_ast.comment = self.tokenstream.print_start_to_end()
        final_value_ast = self.parse_expression(to_downto_ast)
        to_downto_ast.children.append(final_value_ast)
        return_ast.children.append(to_downto_ast)
        self.get_expected_token(TokenType.DO)
        self.tokenstream.set_end_print_position()
        return_ast.comment = self.tokenstream.print_start_to_end()

        if self.tokenstream.peek_token_type() == TokenType.SEMICOLON:
            # Special case <empty-statement>
            no_op_token = Token(TokenType.EMPTY_TOKEN, self.tokenstream.peek_token().location, '')
            return_ast.children.append(AST(no_op_token, return_ast))
        else:
            return_ast.children.append(self.parse_statement(return_ast))

        return return_ast

    def parse_repetitive_statement(self, parent_ast):
        # 6.8.3.6 - <repetitive-statement> ::= <repeat-statement> | <while-statement> | <for-statement>
        assert self.tokenstream.peek_token_type() in (TokenType.WHILE, TokenType.REPEAT, TokenType.FOR), \
            "Parser.parse_repetitive_statement: called for token that is not While, Repeat, or For"

        # while and repeat are supported
        if self.tokenstream.peek_token_type() == TokenType.WHILE:
            return_ast = self.parse_while_statement(parent_ast)
        elif self.tokenstream.peek_token_type() == TokenType.REPEAT:
            return_ast = self.parse_repeat_statement(parent_ast)
        else:
            return_ast = self.parse_for_statement(parent_ast)
        return return_ast

    def parse_structured_statement(self, parent_ast):
        # 6.8.3.1 - <structured-statement> ::= <compound-statement> | <conditional-statement>
        #                                       | <repetitive-statement> | <with-statement>

        # with-statement is not currently supported.
        # while-statement and repeat-statement are the repetitive statements supported.

        if self.tokenstream.peek_token_type() == TokenType.BEGIN:
            return self.parse_compound_statement(parent_ast)
        elif self.tokenstream.peek_token_type() in (TokenType.WHILE, TokenType.REPEAT, TokenType.FOR):
            return self.parse_repetitive_statement(parent_ast)
        else:
            return self.parse_conditional_statement(parent_ast)

    def parse_statement(self, parent_ast):
        # 6.8.1 - <statement> ::= [<label>:] (<simple-statement> | <structured-statement>)
        # labels are not yet supported
        assert parent_ast is not None

        next_token_type = self.tokenstream.peek_token_type()
        if starts_structured_statement(next_token_type):
            return self.parse_structured_statement(parent_ast)
        else:
            return self.parse_simple_statement(parent_ast)

    def parse_statement_sequence(self, end_token_type, current_ast):
        # 6.8.3.1 - <statement-sequence> ::= <statement> [ ";" <statement> ]
        # 6.8.1 - <statement> ::= [<label>:] (<simple-statement> | <structured-statement>)
        # 6.8.2.1 - <simple-statement> ::= <empty-statement> | <assignment-statement> | <procedure-statement>
        #                                   | <goto-statement>
        #
        # Statement sequences are, as they are named, sequences of statements.  However,
        # the end of the sequence is denoted by different tokens depending on where the
        # statement sequence is embedded.  Two examples are compound-statement, which is
        # "begin" <statement-sequence> "end" and the repeat-statement, which is
        # "repeat" <statement-sequence> "until."

        # Since the first <statement> in the <statement-sequence>could be <empty-statement>, check to see if the
        # end_token_type is the next token and, if so, exit.
        if self.tokenstream.peek_token_type() == end_token_type:
            return

        # current_ast is the location where the children should be added
        current_ast.children.append(self.parse_statement(current_ast))
        while self.tokenstream.peek_token_type() == TokenType.SEMICOLON:
            self.get_expected_token(TokenType.SEMICOLON)
            if self.tokenstream.peek_token_type() != end_token_type:
                current_ast.children.append(self.parse_statement(current_ast))
            if self.tokenstream.peek_token_type() != TokenType.SEMICOLON \
                    and self.tokenstream.peek_token_type() != end_token_type:
                # TODO - insert a semicolon into the stream and allow parsing to continue
                # special case error if we don't see the end token and don't see a semicolon
                # TODO - for both Semicolon expected errors, need to show the previous line too.
                raise ParseException(compiler_error_str("Semicolon expected", self.tokenstream.peek_previous_token()))

    def parse_compound_statement(self, parent_ast):
        # 6.8.3.2 - <compound-statement> ::= "begin" <statement-sequence> "end"
        # This function returns an AST node using the BEGIN as the token, and with one child for each
        # statement.
        return_ast = AST(self.get_expected_token(TokenType.BEGIN), parent_ast)
        self.parse_statement_sequence(TokenType.END, return_ast)

        # The expected token here is an END.  However, if the END does not appear, we will try to keep parsing
        # so that other parse errors could be displayed later.  It is frustrating for an end user to have
        # compilation die on the first error.
        end_token = self.tokenstream.eat_token()
        if end_token.token_type != TokenType.END:
            error_str = compiler_error_str("Expected 'end' but saw '{0}'".format(str(end_token.value)), end_token)
            self.parse_error_list.append(error_str)
            while end_token.token_type != TokenType.END:
                try:
                    end_token = self.tokenstream.eat_token()
                except LexerException as e:
                    self.parse_error_list.append(str(e))
                    return return_ast
        return return_ast

    def parse_statement_part(self, parent_ast):
        # 6.2.1 defines statement-part simply as <statement-part> ::= <compound-statement>

        # The <statement-part> is the only portion of the <block> that is required.  Each of the
        # other parts, i.e. label declaration, constant definition, type definition, variable declaration
        # and procedure/function declaration are optional.
        return self.parse_compound_statement(parent_ast)

    def parse_block(self, parent_ast):
        # 6.2.1 of the ISO standard defines a block.  The BNF:
        # <block> ::= <label-declaration-part> <constant-definition-part> <type-definition-part>
        #             <variable-declaration-part> <procedure-and-function-declaration-part>
        #             <statement-part>
        # Unlike the rest of the parse_* functions, this one returns a list of AST nodes to become the
        # children of the AST being returned by the calling function.

        return_ast_list = []

        label_ast_list = self.parse_label_declaration_part(parent_ast)
        return_ast_list.extend(label_ast_list)

        # parse_constant_definition_part updates the literal and symbol tables, does not return anything to add to AST.
        self.parse_constant_definition_part(parent_ast)

        # parse_type_definition_part updates the symbol table, does not return anything to be added to the AST
        self.parse_type_definition_part(parent_ast)

        # parse_variable_declaration_part updates the symbol table, it does not return anything to be added to the AST.
        self.parse_variable_declaration_part(parent_ast)

        procedure_function_ast_list = self.parse_procedure_and_function_declaration_part(parent_ast)
        return_ast_list.extend(procedure_function_ast_list)
        # Only the <statement-part> is required; other parts above are optional
        statement_ast = self.parse_statement_part(parent_ast)
        return_ast_list.append(statement_ast)

        return return_ast_list

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

        return_ast = AST(self.get_expected_token(TokenType.PROGRAM), None)
        # this will be the symbol table for globals
        return_ast.init_symbol_table()
        # currently we do not do anything with the program name, so no need to assign get_expected_token to a value
        self.get_expected_token(TokenType.IDENTIFIER)
        if self.tokenstream.peek_token_type() == TokenType.LEFT_PAREN:
            position = 1
            self.get_expected_token(TokenType.LEFT_PAREN)
            while self.tokenstream.peek_token_type() != TokenType.RIGHT_PAREN:
                self.override_next_identifier_to_required_identifier_if_needed(return_ast)
                token = self.tokenstream.eat_token()
                if token.token_type == TokenType.INPUT:
                    # TODO - this adding the ProgramParameterSymbol separate from the type identifier into symbol_table
                    # is not consistent with how we add other types like integer, real, etc.  Probably need to add
                    # "text" when we add the simple types, and then have text_file_type.denoter = the text base type?
                    # Not sure.
                    text_file_type = pascaltypes.TextFileType("input")
                    return_ast.symbol_table.add(ProgramParameterSymbol("input", token.location, text_file_type, None))
                elif token.token_type == TokenType.OUTPUT:
                    text_file_type = pascaltypes.TextFileType("output")
                    return_ast.symbol_table.add(ProgramParameterSymbol("output", token.location, text_file_type, None))
                elif token.token_type == TokenType.IDENTIFIER:
                    # when we run into the definition of this, we will change the component type if it is not text
                    file_type = pascaltypes.FileType(token.value, pascaltypes.CharacterType())
                    return_ast.symbol_table.add(
                        ProgramParameterSymbol(token.value, token.location, file_type, position))
                    position += 1
                else:
                    raise ParseException(
                        compiler_error_str("Invalid program parameter '{}'".format(token.value), token))
                if self.tokenstream.peek_token_type() != TokenType.RIGHT_PAREN:
                    self.get_expected_token(TokenType.COMMA)
            self.get_expected_token(TokenType.RIGHT_PAREN)
        self.get_expected_token(TokenType.SEMICOLON)
        return_ast.children = self.parse_block(return_ast)
        self.get_expected_token(TokenType.PERIOD)
        return return_ast

    def parse(self):
        self.tokenstream.reset_position()
        self.AST = self.parse_program()
        if len(self.parse_error_list) > 0:  # pragma: no cover
            # We currently end on first parse error.  If we ever leverage parse_error_list then remove the pragma
            for e in self.parse_error_list:
                print(e)
            raise ParseException("Parsing Failed")
