"""
    TAC = Three-Address Code.  A form of intermediate representation (IR) which resembles assembly language.
    While we could compile directly from an Abstract Syntax Tree, using TAC gives a compiler writer several
    advantages.

    1) Optimization - there are numerous optimizations that can be much more easily performed on TAC
    than an AST.

    2) Portability - it is easy to build a retargetable compiler by having the front-end compile down to
    TAC, and then build several back-ends that translate the optimized TAC to the language of the target
    processor / operating system.  Similarly, if you have a set of back-ends that take TAC and compile to
    a specific target, then a new front-end that could compile to TAC could take advantage of all the targets.
    The TAC optimizer could be a standalone bridge between the two.

    3) Debugging - one could build an interpreter that executed TAC as if it were a machine of its own.  This
    allows isolating front-end bugs from back-end assembly language generation defects.

    Reference:
        https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/lectures/13/Slides13.pdf
        https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/handouts/240%20TAC%20Examples.pdf


    Supported TAC operators:
        Assignment (:=)
        Math (+, -, *, /)
        Boolean (>, >=, <, <=, =, <>)

        Note - boolean expressions evaluate to either 0 or 1.  So, (a < b) will be 1 if a is indeed less than
        b, or 0 if a is greater than or equal to b.


    TAC also supports:
        Labels - similar to assembly, just an identifier followed by a colon
        Goto - transfers control to statement named by a label
        If {boolean expression} Goto {label} - if the expression is true, then goto the statement named by the label

    Functions / Procedures
        If a Procedure or Function takes parameters, then before the call to the function or procedure, one or more
        "param" calls will be made.  After the parameters are
        indicated, then a "Call" statement is executed with two parameters: first being the label corresponding to the
        function or procedure, second being the number of parameters being passed.  Most recent N parameters will
        get passed to that func/proc.  At the end of a procedure, the statement "return" occurs; if a function then
        it would be "return" followed by the value being returned.  At the start of a procedure or function,
        a "BeginFunc" statement followed by a number of bytes.  This sums up the number of bytes needed for all
        local variables and all temporaries.

        After calling a procedure or function, there must be a "clear param" statement.  This will be used if
        parameters are pushed onto the stack.

    Other TAC commands:
        setjmp - must be the statement immediately before a label.  Used if a non-local goto might reference the
        label.
        longjmp - a statement followed by a label name.  Similar to goto, but used if transferring control to
        a non-local label.

        WriteI - takes an integer argument, writes it to standard output
        WriteS - takes a string literal argument, writes it to standard output
        WriteAC - takes an array of characters and writes it to standard output
        WriteC - takes a single character and writes it to standard output
        WriteB - takes a boolean and writes either True or False to standard output
        WriteLF - writes a newline character to standard output

    TODO:
        Memory allocation (new/dispose)
        Read/Readln from console
        Read/Write from/to files
"""

from enum import Enum, unique
from copy import deepcopy
from parser import AST, is_relational_operator, is_iso_required_function
from symboltable import Symbol, Label, Literal, IntegerLiteral, RealLiteral, StringLiteral, BooleanLiteral, \
    SymbolTable, LiteralTable, ActivationSymbol, Parameter, VariableSymbol, \
    FunctionResultVariableSymbol, ConstantSymbol, CharacterLiteral
from lexer import TokenType, Token
from compiler_error import compiler_error_str, compiler_warn_str, compiler_fail_str
import pascaltypes


class TACException(Exception):
    pass


@unique
class TACOperator(Enum):
    LABEL = "label"
    ASSIGN = ":="
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    INTEGER_DIV = "div"
    MOD = "mod"
    EQUALS = "="
    NOT_EQUAL = "<>"
    LESS = "<"
    LESS_EQUAL = "<="
    GREATER = ">"
    GREATER_EQUAL = ">="
    ASSIGN_ADDRESS_OF = ":= &"
    ASSIGN_TO_DEREFERENCE = "* :="
    ASSIGN_DEREFERENCE_TO = ":= *"
    AND = "and"
    OR = "or"
    NOT = "not"
    PARAM = "param"
    CALL = "call"
    COMMENT = "comment"
    INT_TO_REAL = "is int_to_real"
    IFZ = "ifz"
    GOTO = "goto"
    RETURN = "return"

    def __str__(self):
        return self.value


def map_token_type_to_tac_operator(token_type):
    # Token Types have equivalent TACOperators, this is a mapping
    assert isinstance(token_type, TokenType)
    assert token_type in (TokenType.EQUALS, TokenType.NOTEQUAL, TokenType.LESS, TokenType.LESS_EQUAL, TokenType.GREATER,
                          TokenType.GREATER_EQUAL, TokenType.INTEGER_DIV, TokenType.MOD, TokenType.MULTIPLY,
                          TokenType.PLUS, TokenType.MINUS, TokenType.DIVIDE, TokenType.AND, TokenType.OR, TokenType.NOT)
    if token_type == TokenType.EQUALS:
        ret = TACOperator.EQUALS
    elif token_type == TokenType.NOTEQUAL:
        ret = TACOperator.NOT_EQUAL
    elif token_type == TokenType.LESS:
        ret = TACOperator.LESS
    elif token_type == TokenType.LESS_EQUAL:
        ret = TACOperator.LESS_EQUAL
    elif token_type == TokenType.GREATER:
        ret = TACOperator.GREATER
    elif token_type == TokenType.GREATER_EQUAL:
        ret = TACOperator.GREATER_EQUAL
    elif token_type == TokenType.NOT:
        ret = TACOperator.NOT
    elif token_type == TokenType.AND:
        ret = TACOperator.AND
    elif token_type == TokenType.OR:
        ret = TACOperator.OR
    elif token_type == TokenType.INTEGER_DIV:
        ret = TACOperator.INTEGER_DIV
    elif token_type == TokenType.MOD:
        ret = TACOperator.MOD
    elif token_type == TokenType.MULTIPLY:
        ret = TACOperator.MULTIPLY
    elif token_type == TokenType.PLUS:
        ret = TACOperator.ADD
    elif token_type == TokenType.MINUS:
        ret = TACOperator.SUBTRACT
    else:
        assert token_type == TokenType.DIVIDE
        ret = TACOperator.DIVIDE
    return ret


def invalid_parameter_for_system_function_error_str(token, str_required_types):
    assert isinstance(token, Token)
    return "Function {}() requires {} parameter in {}".format(token.token_type, str_required_types, token.location)


def required_function_accepts_real(token_type):
    # The arithmetic functions in 6.6.6.2 all accept reals as do the transfer functions in 6.6.6.3.
    assert isinstance(token_type, TokenType)
    if token_type in (TokenType.ABS, TokenType.SQR, TokenType.SIN, TokenType.COS, TokenType.EXP,
                      TokenType.LN, TokenType.SQRT, TokenType.ARCTAN, TokenType.TRUNC, TokenType.ROUND):
        return True
    else:
        return False


def required_function_accepts_integer(token_type):
    # abs() and sqr() in 6.6.6.2, chr() in 6.6.6.4, and odd() from 6.6.6.5 accept integers
    assert isinstance(token_type, TokenType)
    if token_type in (TokenType.ABS, TokenType.SQR, TokenType.CHR, TokenType.ODD):
        return True
    else:
        return False


def required_function_accepts_integer_or_real(token_type):
    # abs() and sqr() in 6.6.6.2 accept both integer or real
    assert isinstance(token_type, TokenType)
    if token_type in (TokenType.ABS, TokenType.SQR):
        return True
    else:
        return False


def required_function_accepts_ordinal(token_type):
    # ord(), succ(), pred() in 6.6.6.4 accept ordinals
    assert isinstance(token_type, TokenType)
    if token_type in (TokenType.ORD, TokenType.SUCC, TokenType.PRED):
        return True
    else:
        return False


def required_function_return_type(token_type, parameter_type):
    # abs() and sqr() in 6.6.6.2 as well as succ() and pred() in 6.6.6.4 return same type as parameter
    # Remaining functions in 6.6.6.2 return reals
    # Transfer functions in 6.6.6.3 return ints
    # ord() in 6.6.6.4 returns int.
    # chr() in 6.6.6.4 returns char
    # functions in 6.6.6.5 return Boolean
    if token_type in (TokenType.ABS, TokenType.SQR, TokenType.SUCC, TokenType.PRED):
        # this is a bit of hackery but it works
        return_type = deepcopy(parameter_type)
    elif token_type in (TokenType.SIN, TokenType.COS, TokenType.EXP, TokenType.LN, TokenType.SQRT, TokenType.ARCTAN):
        return_type = pascaltypes.RealType()
    elif token_type in (TokenType.TRUNC, TokenType.ROUND, TokenType.ORD):
        return_type = pascaltypes.IntegerType()
    elif token_type == TokenType.CHR:
        return_type = pascaltypes.CharacterType()
    else:
        assert token_type in (TokenType.ODD, TokenType.EOF, TokenType.EOLN)
        return_type = pascaltypes.BooleanType()
    return return_type


def map_token_to_system_function_name(token, type_str):
    assert isinstance(token, Token)
    return "_{}_{}".format(str(token.token_type).upper(), type_str.upper())


class TACNode:
    def __init__(self, operator):
        assert isinstance(operator, TACOperator)
        self.operator = operator


class TACCommentNode(TACNode):
    def __init__(self, comment):
        assert isinstance(comment, str)
        super().__init__(TACOperator.COMMENT)
        self.comment = comment

    def __str__(self):  # pragma: no cover
        return "\t\t;{}".format(self.comment)


class TACNoOpNode(TACCommentNode):
    def __init__(self):
        super().__init__('NO-OP')


class TACLabelNode(TACNode):
    def __init__(self, label, comment=None):
        assert isinstance(label, Label)
        assert comment is None or isinstance(comment, str)
        super().__init__(TACOperator.LABEL)
        self.label = label
        self.comment = comment

    def __str__(self):  # pragma: no cover
        return "{}:".format(self.label)


class TACFunctionReturnNode(TACNode):
    def __init__(self, return_value):
        assert return_value is None or isinstance(return_value, Symbol)
        super().__init__(TACOperator.RETURN)
        self.return_value = return_value

    def __str__(self):  # pragma: no cover
        return_str = "return"
        if self.return_value is not None:
            return_str += " " + str(self.return_value)
        return return_str


class TACParamNode(TACNode):
    def __init__(self, parameter_value):
        # TODO - what about other literal types?
        assert isinstance(parameter_value, Symbol) or isinstance(parameter_value, IntegerLiteral)
        super().__init__(TACOperator.PARAM)
        self.parameter_value = parameter_value

    def __str__(self):  # pragma: no cover
        return "{} {}".format(str(self.operator), str(self.parameter_value))


class TACCallFunctionNode(TACNode):
    def __init__(self, label, function_name, number_of_parameters, left_value=None):
        assert isinstance(label, Label)
        assert isinstance(number_of_parameters, int)
        assert isinstance(function_name, str)
        assert left_value is None or isinstance(left_value, Symbol)
        assert number_of_parameters >= 0
        super().__init__(TACOperator.CALL)
        self.label = label
        self.function_name = function_name
        self.number_of_parameters = number_of_parameters
        self.left_value = left_value

    def __str__(self):  # pragma: no cover
        if self.left_value is None:
            return "{} {} [{}] {}".format(str(self.operator), self.label, self.function_name,
                                          str(self.number_of_parameters))
        else:
            return "{} := {} {} [{}]".format(str(self.left_value), str(self.operator),
                                             self.label, self.function_name, str(self.number_of_parameters))


class TACCallSystemFunctionNode(TACCallFunctionNode):
    def __init__(self, label, number_of_parameters, left_value=None):
        assert isinstance(label, Label)
        super().__init__(label, label.name, number_of_parameters, left_value)


class TACUnaryNode(TACNode):
    def __init__(self, left_value, operator, argument):
        assert isinstance(argument, Symbol)
        assert isinstance(left_value, Symbol)
        super().__init__(operator)
        self.left_value = left_value
        self.argument = argument

    def __str__(self):  # pragma: no cover
        return "{} {} {}".format(str(self.left_value), str(self.operator), str(self.argument))


class TACUnaryLiteralNode(TACNode):
    def __init__(self, left_value, operator, literal):
        assert isinstance(left_value, Symbol)
        assert isinstance(literal, Literal)
        super().__init__(operator)
        self.left_value = left_value
        self.literal = literal

    def __str__(self):  # pragma: no cover
        if isinstance(self.literal, StringLiteral) or isinstance(self.literal, CharacterLiteral):
            literal_value = '"{}"'.format(str(self.literal).replace('"', '\"'))
        else:
            literal_value = str(self.literal)
        return "{} {} {}".format(str(self.left_value), str(self.operator), literal_value)


class TACBinaryNode(TACNode):
    def __init__(self, result, operator, argument1, argument2):
        assert isinstance(result, Symbol)
        # todo - what about other literal types?
        assert isinstance(argument1, Symbol) or isinstance(argument1, IntegerLiteral)
        assert isinstance(argument2, Symbol) or isinstance(argument2, IntegerLiteral)
        super().__init__(operator)
        self.result = result
        self.argument1 = argument1
        self.argument2 = argument2

    def __str__(self):  # pragma: no cover
        return "{} := {} {} {}".format(str(self.result), str(self.argument1), str(self.operator), str(self.argument2))


class TACBinaryNodeWithBoundsCheck(TACBinaryNode):
    def __init__(self, result, operator, argument1, argument2, lower_bound, upper_bound):
        # Note - this is possibly a hack, because it's 5 arguments, but the alternative is to do a much longer
        # string where I get the result, then write the explicit test for less than the min and greater than the
        # max and throw the runtime error from within the TAC.  It would be the first runtime error enforced in the
        # TAC, so I don't want to extend the TAC to do that right now.
        assert isinstance(argument1, Symbol)
        assert isinstance(argument1.pascal_type, pascaltypes.PointerType)
        assert isinstance(lower_bound, int)
        assert isinstance(upper_bound, int)
        super().__init__(result, operator, argument1, argument2)
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def __str__(self):  # pragma: no cover
        ret = super().__str__()
        ret += " ; {} must have lower_bound {} and upper_bound {}"
        ret = ret.format(self.argument2.name, self.lower_bound, self.upper_bound)
        return ret


class TACGotoNode(TACNode):
    def __init__(self, label):
        assert isinstance(label, Label)
        super().__init__(TACOperator.GOTO)
        self.label = label

    def __str__(self):  # pragma: no cover
        return "{} {}".format(str(self.operator), str(self.label))


class TACIFZNode(TACNode):
    def __init__(self, value, label):
        assert isinstance(value, Symbol)
        assert isinstance(label, Label)
        super().__init__(TACOperator.IFZ)
        self.value = value
        self.label = label

    def __str__(self):  # pragma: no cover
        return "{} {} GOTO {}".format(str(self.operator), str(self.value), str(self.label))


class TACBlock:
    """ For now, assume a TACBlock represents a Pascal Block.  Not entirely language-independent but
    will work.

    NOTE: For it really to be a Pascal block, we will need to have TACBlocks within TACBlocks when
    we allow procedures and functions to be declared within another procedure or function.  This
    could in theory be done with a TACNode that contains a TACBlock?  Need to figure that out later.

    Purpose of having the generator as a member variable is so that the get_label() / get_temporary()
    can leverage the counters in the generator.
    """

    def __init__(self, ismain, generator):
        assert isinstance(ismain, bool)
        assert isinstance(generator, TACGenerator)
        self.is_main = ismain
        self.tacnodes = []
        self.symbol_table = SymbolTable()
        self.parameter_list = None
        self.generator = generator

    def get_label(self, label_suffix=""):
        return self.generator.get_label(label_suffix)

    def get_temporary(self):
        return self.generator.get_temporary()

    def add_node(self, node):
        assert isinstance(node, TACNode)
        self.tacnodes.append(node)

    def print_nodes(self):  # pragma: no cover
        for node in self.tacnodes:
            print(str(node))

    def process_ast_begin(self, ast):
        assert isinstance(ast, AST)
        for child in ast.children:
            self.process_ast(child)

    def dereference_if_needed(self, symbol, symbol_use_token=None):
        assert isinstance(symbol, Symbol) or isinstance(symbol, Literal)
        assert symbol_use_token is None or isinstance(symbol_use_token, Token)
        if isinstance(symbol, Literal):
            return symbol
        elif isinstance(symbol.pascal_type, pascaltypes.PointerType):
            # TODO - this works fine now when the only pointers we use are arrays.  But once we have actual pointers,
            # we won't necessarily want to deref them.  So we will need a way to test whether the sym is a real pointer
            # or a pointer to an array value.  Maybe a subclass off of pascaltypes.PointerType?

            # make a new symbol that has as its base type, the base type of the pointer
            # assign deref of the pointer to the new symbol.
            base_type_symbol = Symbol(self.get_temporary(), symbol.location, symbol.pascal_type.points_to_type)
            self.symbol_table.add(base_type_symbol)
            self.add_node(TACUnaryNode(base_type_symbol, TACOperator.ASSIGN_DEREFERENCE_TO, symbol))
            return base_type_symbol
        else:
            if isinstance(symbol, VariableSymbol) and not symbol.is_assigned_to:
                if self.is_main or self.symbol_table.exists_prior_to_global_scope(symbol.name):
                    if symbol_use_token is not None:
                        # if a and b are arrays of same type, "a := b" is legal syntax, but code won't assign to
                        # b.  It would assign to the array elements.  So we exclude warning on an array assignment.
                        if not isinstance(symbol.pascal_type, pascaltypes.ArrayType):
                            if symbol.was_assigned_to:
                                warning_str = compiler_warn_str(
                                    "Variable possibly used when undefined: {}".format(symbol_use_token.value),
                                    symbol_use_token)
                            else:
                                warning_str = compiler_warn_str(
                                    "Variable possibly used before assignment: {}".format(symbol_use_token.value),
                                    symbol_use_token)
                            self.generator.warnings_list.append(warning_str)
            return symbol

    def process_ast_goto(self, ast):
        # Right now, this only handles system gotos, specifically for one type of runtime
        # error.  When this is user-written gotos, then we need to add handling for
        # user-defined labels.
        assert isinstance(ast, AST), compiler_fail_str("tac_ir.process_ast_goto: ast is not an AST")
        assert ast.token.token_type == TokenType.GOTO, compiler_fail_str(
            "tac_ir.process_ast_goto: cannot process non-goto")
        assert len(ast.children) == 1, compiler_fail_str("tac_ir.process_ast_goto: goto statements must have 1 child")
        assert ast.children[0].token.token_type == TokenType.LABEL, compiler_fail_str(
            "tac_ir.process_ast_goto: goto must have label destination")

        label = Label(ast.children[0].token.value)
        self.add_node(TACGotoNode(label))

    def track_function_return_value_assignments(self, return_value_symbol, return_value_is_assigned_symbol, ast):
        # 6.7.3 of the ISO standard states that it shall be an error if the result of a function is undefined
        # upon completion of the algorithm.  This function inserts the runtime checks to varify the result
        # is assigned.  We also validate at compile time that there is at least one assignment statement with the
        # function-identifier is on the left side.  The return value of this proc is true if this ast is an assignment
        # to the function result or if any of the ast's children are.
        #
        # Per Cooper, p.77: "Every function must contain at least one assignment to its identifier."  Also,
        # "[T]he function-identifier alone ... represents a storage location ... that may only be assigned to."
        # I infer from this that you cannot set the return value of a function by passing the function-identifier
        # to a procedure as a by_ref argument or such.

        assert isinstance(return_value_symbol, FunctionResultVariableSymbol), (
            compiler_fail_str("tac_ir.track_function_return_value_assignment: return_value_symbol is not a symbol"))
        assert isinstance(return_value_is_assigned_symbol, VariableSymbol), (
            compiler_fail_str(
                "tac_ir.track_function_return_value_assignment: return_value_is_assigned_symbol is not a symbol"))
        assert isinstance(ast, AST), compiler_fail_str(
            "tac_ir.track_function_return_value_assignment: ast is not an AST")

        retval = False
        if ast.token.token_type == TokenType.ASSIGNMENT:
            if ast.nearest_symbol_table().exists(ast.children[0].token.value.lower()):
                left_value_symbol = ast.nearest_symbol_table().fetch(ast.children[0].token.value.lower())
                if left_value_symbol is return_value_symbol:
                    new_begin = AST(Token(TokenType.BEGIN, ast.token.location, "Begin"), ast.parent,
                                    "Track assignment to {}".format(return_value_symbol.name))
                    ast.parent = new_begin
                    new_begin.children.append(ast)
                    track_assignment_ast = AST(Token(TokenType.ASSIGNMENT, ast.children[0].token.location, ":="),
                                               new_begin,
                                               "Assign {} to true".format(return_value_is_assigned_symbol.name))
                    left_value_token = Token(TokenType.IDENTIFIER, ast.children[0].token.location,
                                             return_value_is_assigned_symbol.name)
                    true_token = Token(TokenType.TRUE, ast.children[0].token.location, 'true')
                    track_assignment_ast.children.append(AST(left_value_token, track_assignment_ast))
                    track_assignment_ast.children.append(AST(true_token, track_assignment_ast))
                    new_begin.children.append(track_assignment_ast)
                    new_begin.parent.children[new_begin.parent.children.index(new_begin.children[0])] = new_begin
                    retval = True
        else:
            for child in ast.children:
                if self.track_function_return_value_assignments(return_value_symbol, return_value_is_assigned_symbol,
                                                                child):
                    retval = True
        return retval

    def process_ast_procedure_or_function(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.PROCEDURE, TokenType.FUNCTION)

        # TODO - when we want to have procedures declared within procedures, this next line will fail.
        # For now, we're ensuring the Procedure/Function is the first TACNode in the list.  This
        # matters because we are going to copy the parameter list from the AST to the TACBlock
        # and cannot do that if we have multiple parameter lists for nested procs.
        # We need some other structure.
        assert len(self.tacnodes) == 0, compiler_fail_str("tac_ir.process_ast_procedure_or_function:" +
                                                          " cannot declare functions or procedures inside other " +
                                                          "functions or procedures yet")

        # first child of a Procedure or Function is an identifier with the name of the proc/func
        assert len(ast.children) >= 1, compiler_fail_str(
            "tac_id.process_ast_procedure_or_function: procedure/function with no children")
        assert ast.children[0].token.token_type == TokenType.IDENTIFIER, compiler_fail_str(
            "tac_ir.process_ast_procedure_or_function: first child of procedure/function must be an identifier")

        token = ast.token
        procedure_name = ast.children[0].token.value

        self.parameter_list = ast.parameter_list
        # need to copy each parameter into the SymbolTable.  If the parameter is a variable parameter (ByRef),
        # the type of the symbol is a pointer to the type of the Parameter.  If the parameter is a value
        # parameter (ByVal) then the type of symbol is same as type of Parameter.
        # Remember also - Parameter Lists are ordered, but Symbol Tables are not.
        for param in self.parameter_list.parameter_list:
            assert isinstance(param, Parameter)
            temp_symbol = deepcopy(param.symbol)
            temp_symbol.is_assigned_to = True
            self.symbol_table.add(temp_symbol)

        # we need to go to the parent to fetch the activation symbol.  If we do the fetch on
        # the current node, and this is a function, we will instead get the symbol that would hold the result.
        activation_symbol = self.symbol_table.parent.fetch(procedure_name)
        assert isinstance(activation_symbol, ActivationSymbol)
        activation_label = self.get_label(procedure_name)
        activation_symbol.label = activation_label
        if token.token_type == TokenType.FUNCTION:
            if len(ast.children) < 2:
                error_str = 'Error D.48: Function {} must have a return value'.format(procedure_name)
                raise TACException(compiler_error_str(error_str, token))
            comment = "Function {}({})".format(procedure_name, str(self.parameter_list))
            # Error D.48 states "It is an error if the result of an activation of a function is undefined upon
            # completion of the function."  At compile time, we can validate that there is at least one assignment
            # statement, but we cannot validate, in the general case, that it executes.  We need to track at runtime
            # whether the return value is ever assigned.  This local variable will do that.  Beginning name with
            # underscore ensures it will not collide with any user-defined identifier.

            # create a variable to track that retval is assigned
            return_value_is_assigned_variable_name = '_{}_is_assigned'.format(procedure_name)
            return_value_is_assigned_symbol = VariableSymbol(return_value_is_assigned_variable_name, token.location,
                                                             pascaltypes.BooleanType())
            self.symbol_table.add(return_value_is_assigned_symbol)
            ast.symbol_table.add(return_value_is_assigned_symbol)

            # create an AST that initializes this variable to False, and make that the first statement executed
            # in the current AST.
            return_value_is_assigned_initialization_ast = AST(Token(TokenType.ASSIGNMENT, None, ":="), ast,
                                                              "initialize {} to false".format(
                                                                  return_value_is_assigned_variable_name))
            return_value_is_assigned_token = Token(TokenType.IDENTIFIER, token.location,
                                                   return_value_is_assigned_variable_name)
            false_token = Token(TokenType.FALSE, token.location, 'false')
            return_value_is_assigned_initialization_ast.children.append(
                AST(return_value_is_assigned_token, return_value_is_assigned_initialization_ast))
            return_value_is_assigned_initialization_ast.children.append(
                AST(false_token, return_value_is_assigned_initialization_ast))
            # make this assignment become the first statement in the function
            ast.children[1].children.insert(0, return_value_is_assigned_initialization_ast)

            # recursively iterate through the children of the current AST, starting with the one following the
            # assignment we just inserted, and identify any assignments to the retval.  This requires matching on
            # the symbols themselves, not the names, as function declared inside a function could reuse a name.
            return_value_symbol = ast.symbol_table.fetch(procedure_name)
            is_return_value_ever_set = False
            for grandchild in ast.children[1].children[1:]:
                if self.track_function_return_value_assignments(return_value_symbol, return_value_is_assigned_symbol,
                                                                grandchild):
                    is_return_value_ever_set = True

            # check if the return value is assigned to at least once in the ast.
            if not is_return_value_ever_set:
                error_str = 'Error D.48: Function {} must have a return value'.format(procedure_name)
                raise TACException(compiler_error_str(error_str, token))

            # now we need to test that the return value was assigned
            child = ast.children[1]  # only needed to anchor the locations for the ASTs I'm creating below.
            if_assigned_ast = AST(Token(TokenType.IF, child.token.location, 'if'), ast,
                                  'if {} = False, then error'.format(return_value_is_assigned_variable_name))
            equals_test_ast = AST(Token(TokenType.EQUALS, child.token.location, '='), if_assigned_ast,
                                  'if {} = false'.format(return_value_is_assigned_variable_name))
            # I could probably reuse these tokens, but I'm very conservative
            equals_test_ast.children.append(AST(deepcopy(return_value_is_assigned_token), equals_test_ast))
            equals_test_ast.children.append(AST(deepcopy(false_token), equals_test_ast))
            if_assigned_ast.children.append(equals_test_ast)

            goto_ast = AST(Token(TokenType.GOTO, child.token.location, 'goto'), if_assigned_ast,
                           'goto _PASCAL_NO_RETURN_VALUE_ERROR')
            label_ast = AST(Token(TokenType.LABEL, child.token.location, '_PASCAL_NO_RETURN_VALUE_ERROR'), goto_ast,
                            '_PASCAL_NO_RETURN_VALUE_ERROR')
            goto_ast.children.append(label_ast)
            if_assigned_ast.children.append(goto_ast)

            ast.children.append(if_assigned_ast)
        else:
            comment = "Procedure {}({})".format(procedure_name, str(self.parameter_list))
        self.add_node(TACLabelNode(activation_label, comment))

        for child in ast.children[1:]:
            self.process_ast(child)

        if token.token_type == TokenType.FUNCTION:
            self.add_node(TACFunctionReturnNode(self.symbol_table.fetch(procedure_name)))
        else:
            self.add_node(TACFunctionReturnNode(None))

    def process_ast_iso_required_function(self, ast):
        assert isinstance(ast, AST)
        assert is_iso_required_function(ast.token.token_type)

        iso_function_token = ast.token
        ast_left_value_symbol_or_literal = self.dereference_if_needed(self.process_ast(ast.children[0]),
                                                                      ast.children[0].token)
        tac_left_value_symbol = Symbol(self.get_temporary(), iso_function_token.location,
                                       required_function_return_type(iso_function_token.token_type,
                                                                     ast_left_value_symbol_or_literal.pascal_type))
        self.symbol_table.add(tac_left_value_symbol)
        if required_function_accepts_ordinal(iso_function_token.token_type):
            if isinstance(ast_left_value_symbol_or_literal.pascal_type, pascaltypes.OrdinalType):
                self.add_node(TACParamNode(ast_left_value_symbol_or_literal))
                self.add_node(
                    TACCallSystemFunctionNode(Label(map_token_to_system_function_name(iso_function_token, "ORDINAL")),
                                              1,
                                              tac_left_value_symbol))
            else:
                raise TACException(
                    compiler_error_str(
                        'Function {}() requires parameter of ordinal type'.format(iso_function_token.token_type),
                        iso_function_token))

        elif required_function_accepts_integer_or_real(iso_function_token.token_type):
            if pascaltypes.is_integer_or_subrange_of_integer(ast_left_value_symbol_or_literal.pascal_type):
                self.add_node(TACParamNode(ast_left_value_symbol_or_literal))
                self.add_node(
                    TACCallSystemFunctionNode(Label(map_token_to_system_function_name(iso_function_token, "INTEGER")),
                                              1,
                                              tac_left_value_symbol))
            elif isinstance(ast_left_value_symbol_or_literal.pascal_type, pascaltypes.RealType):
                self.add_node(TACParamNode(ast_left_value_symbol_or_literal))
                self.add_node(
                    TACCallSystemFunctionNode(Label(map_token_to_system_function_name(iso_function_token, "REAL")), 1,
                                              tac_left_value_symbol))
            else:
                raise TACException(compiler_error_str(
                    'Function {}() requires parameter of integer or real type'.format(iso_function_token.token_type),
                    iso_function_token))
        elif required_function_accepts_integer(iso_function_token.token_type):
            if pascaltypes.is_integer_or_subrange_of_integer(ast_left_value_symbol_or_literal.pascal_type):
                self.add_node(TACParamNode(ast_left_value_symbol_or_literal))
                self.add_node(
                    TACCallSystemFunctionNode(Label(map_token_to_system_function_name(iso_function_token, "INTEGER")),
                                              1,
                                              tac_left_value_symbol))
            else:
                raise TACException(
                    compiler_error_str(
                        'Function {}() requires parameter of integer type'.format(iso_function_token.token_type),
                        iso_function_token))
        else:
            assert required_function_accepts_real(iso_function_token.token_type)
            if isinstance(ast_left_value_symbol_or_literal.pascal_type, pascaltypes.IntegerType):
                tmp2 = self.process_symbol_int_to_real(ast_left_value_symbol_or_literal)
                self.add_node(TACParamNode(tmp2))
                self.add_node(
                    TACCallSystemFunctionNode(Label(map_token_to_system_function_name(iso_function_token, "REAL")), 1,
                                              tac_left_value_symbol))
            elif isinstance(ast_left_value_symbol_or_literal.pascal_type, pascaltypes.RealType):
                self.add_node(TACParamNode(ast_left_value_symbol_or_literal))
                self.add_node(
                    TACCallSystemFunctionNode(Label(map_token_to_system_function_name(iso_function_token, "REAL")), 1,
                                              tac_left_value_symbol))
            else:
                raise TACException(
                    compiler_error_str(
                        'Function {}() requires parameter of real type'.format(iso_function_token.token_type),
                        iso_function_token))
        return tac_left_value_symbol

    def process_write_parameter(self, output_file, parameter_symbol, write_token):
        # write_token is only used for a compiler error message.
        assert isinstance(write_token, Token)
        assert write_token.token_type in [TokenType.WRITE, TokenType.WRITELN]
        assert isinstance(parameter_symbol, Symbol) or isinstance(parameter_symbol, Literal)

        base_type = parameter_symbol.pascal_type

        # p.98 of Cooper states that the constants of enumerated ordinal types (pascaltypes.EnumeratedType)
        # "don't have external character representations, and can't be read or written to or from
        # textfiles - in particular, from the standard input and output."  It would be very easy to
        # display the string representation of the constant when trying to print it out, but we will
        # stick to Cooper for now.  The ISO standard is silent on the topic, per my reading.
        if isinstance(base_type, pascaltypes.SubrangeType):
            base_type = base_type.host_type

        if not (isinstance(base_type, pascaltypes.StringLiteralType) or isinstance(base_type, pascaltypes.RealType) or
                isinstance(base_type, pascaltypes.BooleanType) or isinstance(base_type, pascaltypes.IntegerType) or
                isinstance(base_type, pascaltypes.CharacterType) or
                base_type.is_string_type()):
            # TODO - this error string is ugly, but when we have files and can write arbitrary types, this
            # logic will need to change anyway.
            error_str = "'{}' is of type that cannot be displayed by {}()".format(parameter_symbol.name,
                                                                                  write_token.value)
            raise TACException(compiler_error_str(error_str, write_token))

        self.add_node(TACParamNode(output_file))
        self.add_node(TACParamNode(parameter_symbol))
        if isinstance(base_type, pascaltypes.StringLiteralType):
            self.add_node(TACCallSystemFunctionNode(Label("_WRITE_STRING_LITERAL"), 2))
        elif isinstance(base_type, pascaltypes.RealType):
            self.add_node(TACCallSystemFunctionNode(Label("_WRITE_REAL"), 2))
        elif isinstance(base_type, pascaltypes.BooleanType):
            self.add_node(TACCallSystemFunctionNode(Label("_WRITE_BOOLEAN"), 2))
        elif isinstance(base_type, pascaltypes.IntegerType):
            self.add_node(TACCallSystemFunctionNode(Label("_WRITE_INTEGER"), 2))
        elif base_type.is_string_type():
            self.add_node(TACCallSystemFunctionNode(Label("_WRITE_STRING"), 2))
        else:
            self.add_node(TACCallSystemFunctionNode(Label("_WRITE_CHARACTER"), 2))

    def process_ast_file_procedure(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.RESET, TokenType.REWRITE)
        assert len(ast.children) == 1

        token = ast.token
        parameter_symbol = self.process_ast(ast.children[0])
        if not isinstance(parameter_symbol.pascal_type, pascaltypes.FileType):
            error_str = "Function {}() requires parameter of file type".format(token.token_type)
            raise TACException(compiler_error_str(error_str, token))

        if parameter_symbol.name in ("output", "input"):
            error_str = "Cannot call {}() on built-in textfile {}".format(token.token_type, parameter_symbol.value)
            raise TACException(compiler_error_str(error_str, token))

        self.add_node(TACParamNode(parameter_symbol))

        if not isinstance(parameter_symbol.pascal_type, pascaltypes.TextFileType):
            suffix = "B"
        else:
            suffix = ""

        system_function_name = "_" + token.value.upper() + suffix
        self.add_node(TACCallSystemFunctionNode(Label(system_function_name), 1))

    def process_ast_write(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.WRITE, TokenType.WRITELN)
        token = ast.token

        outputfile = self.symbol_table.fetch("output")
        if len(ast.children) > 0:
            child_symbol = self.dereference_if_needed(self.process_ast(ast.children[0]), ast.children[0].token)
            if isinstance(child_symbol.pascal_type, pascaltypes.FileType):
                outputfile = child_symbol
            else:
                self.process_write_parameter(outputfile, child_symbol, token)

        for child in ast.children[1:]:
            child_symbol = self.dereference_if_needed(self.process_ast(child), child.token)
            self.process_write_parameter(outputfile, child_symbol, token)

        if token.token_type == TokenType.WRITELN:
            self.add_node(TACParamNode(outputfile))
            self.add_node(TACCallSystemFunctionNode(Label("_WRITE_LINE_FEED"), 1))

    def process_ast_conditional_statement(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type == TokenType.IF
        assert len(ast.children) in [2, 3], \
            "TACBlock.process_ast_conditional_statement - IF ASTs must have 2 or 3 children."

        token = ast.token
        label_for_finished = self.get_label()
        condition = self.process_ast(ast.children[0])
        if not isinstance(condition.pascal_type, pascaltypes.BooleanType):
            raise TACException(compiler_error_str("If statements must be followed by Boolean expressions", token))

        if len(ast.children) == 2:
            self.add_node(TACIFZNode(condition, label_for_finished))
            self.process_ast(ast.children[1])
            self.add_node(TACLabelNode(label_for_finished))
        else:
            label_for_else = self.get_label()
            self.add_node(TACIFZNode(condition, label_for_else))
            self.process_ast(ast.children[1])
            self.add_node(TACGotoNode(label_for_finished))
            self.add_node(TACCommentNode("ELSE"))
            self.add_node(TACLabelNode(label_for_else))
            self.process_ast(ast.children[2])
            self.add_node(TACLabelNode(label_for_finished))

    def validate_control_variable_not_threatened(self, control_variable_identifier, ast):
        #
        # No statement S in the ast can exist that threatens the control variable - which is defined as:
        #       a) control variable cannot be the left side (variable access) for an assignment statement
        #       b) control variable cannot be passed as a variable parameter (ByRef) to a procedure or function
        #       c) control variable cannot be passed into read() or readln()
        #       d) control variable is used as a control variable for a nested for statement (as interpreted by
        #          Cooper, p.27
        assert isinstance(ast, AST)

        if ast.token.token_type == TokenType.ASSIGNMENT:
            if ast.children[0].token.value.lower() == control_variable_identifier.lower():
                error_str = "Cannot assign a value to the control variable '{}' of a 'for' statement"
                error_str = error_str.format(control_variable_identifier)
                raise TACException(compiler_error_str(error_str, ast.children[0].token))
            self.validate_control_variable_not_threatened(control_variable_identifier, ast.children[1])
        elif ast.token.token_type == TokenType.IDENTIFIER:
            symbol = self.symbol_table.fetch(ast.token.value)
            if isinstance(symbol, ActivationSymbol):
                # procedure or function call - check to see if any of the parameters are the control variable
                for i in range(0, len(ast.children)):
                    child = ast.children[i]
                    if child.token.value.lower() == control_variable_identifier.lower():
                        if symbol.parameter_list[i].is_by_ref:
                            error_str = "Cannot pass control variable '{}' of a 'for' statement as variable parameter "
                            error_str += "'{}' to '{}'"
                            error_str = error_str.format(control_variable_identifier,
                                                         symbol.parameter_list[i].symbol.name,
                                                         symbol.name)
                            raise TACException(compiler_error_str(error_str, child.token))
        elif ast.token.token_type == TokenType.FOR:
            if ast.children[0].children[0].token.value.lower() == control_variable_identifier.lower():
                error_str = "Cannot use control variable '{}' of a 'for' statement as control variable of nested 'for'"
                error_str = error_str.format(control_variable_identifier)
                raise TACException(compiler_error_str(error_str, ast.children[0].children[0].token))
            else:
                self.validate_control_variable_not_threatened(control_variable_identifier, ast.children[0].children[1])
                self.validate_control_variable_not_threatened(control_variable_identifier, ast.children[1])
                self.validate_control_variable_not_threatened(control_variable_identifier, ast.children[2])
        else:
            for child in ast.children:
                self.validate_control_variable_not_threatened(control_variable_identifier, child)

        return True

    def process_ast_repetitive_statement(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.REPEAT, TokenType.WHILE, TokenType.FOR)

        token = ast.token
        if token.token_type == TokenType.FOR:
            assert len(ast.children) == 3, "TACBlock.process_ast_repetitive_statement: 'for' ASTs must have 3 children"

            # We need to validate that this is a legal "for" statement.  Rules per section 6.8.3.9 include:
            #
            # 1) The control variable must be declared in the variable-declaration-block closest-containing the for
            #    statement.  Cannot use a global variable as a control variable.
            # 2) The control variable must be an ordinal type, and the initial value and final value must be a type
            #    compatible with this type.
            # 3) The initial-value and final-value must be assignment-compatible with the type possessed by the
            #    control variable if the <statement> is actually executed.  This will be a runtime check.
            # 4) No statement S can exist that threatens the control variable - which is defined as:
            #       a) control variable cannot be the left side (variable access) for an assignment statement
            #       b) control variable cannot be passed as a variable parameter (ByRef) to a procedure or function
            #       c) control variable cannot be passed into read() or readln()
            #       d) control variable is used as a control variable for a nested for statement (as interpreted by
            #          Cooper, p.27

            # the FOR statement "for v := e1 to e2 do body" shall be translated to:
            # begin
            #   temp1 = e1
            #   temp2 = e2
            #   if temp1 <= temp2 then begin
            #       v := temp1
            #       body;
            #       while v <> temp2 do begin
            #           v := succ(v);
            #           body;
            #       end
            #   end
            # end
            #
            # "downto" is parsed the same except the <= is >= and the succ() call is replaced with pred()

            # We will build out the for statement, and then enforce the rules from above once we have
            # types for all the symbols.

            assignment_ast = ast.children[0]
            assert len(assignment_ast.children) == 2
            to_or_downto_ast = ast.children[1]
            assert to_or_downto_ast.token.token_type in (TokenType.TO, TokenType.DOWNTO)
            assert len(to_or_downto_ast.children) == 1
            body_ast = ast.children[2]

            # need to assign the initial and final value to temp1 and temp2 so that any changes to variables
            # in the initial and final value have no impact on the for statement.  See Cooper p.28 and p.29
            initial_value = self.process_ast(assignment_ast.children[1])
            temp1 = Symbol(self.get_temporary(), initial_value.location, initial_value.pascal_type)
            self.symbol_table.add(temp1)

            if isinstance(initial_value, IntegerLiteral):
                self.add_node(TACUnaryLiteralNode(temp1, TACOperator.ASSIGN, initial_value))
            else:
                self.add_node(TACUnaryNode(temp1, TACOperator.ASSIGN, initial_value))

            final_value = self.process_ast(to_or_downto_ast.children[0])
            temp2 = Symbol(self.get_temporary(), final_value.location, final_value.pascal_type)
            self.symbol_table.add(temp2)
            if isinstance(final_value, IntegerLiteral):
                self.add_node(TACUnaryLiteralNode(temp2, TACOperator.ASSIGN, final_value))
            else:
                self.add_node(TACUnaryNode(temp2, TACOperator.ASSIGN, final_value))

            control_variable_token = assignment_ast.children[0].token
            assert isinstance(control_variable_token, Token)

            # Enforce rule 1 from above
            if not ast.nearest_symbol_table().exists(control_variable_token.value):
                error_str = "Control variable '{}' must be declared in same block as the 'for'"
                error_str = error_str.format(control_variable_token.value)
                raise TACException(compiler_error_str(error_str, control_variable_token))

            control_variable_symbol = self.symbol_table.fetch(control_variable_token.value)
            control_variable_symbol.is_assigned_to = True
            assert isinstance(control_variable_symbol, Symbol)

            # Enforce rule 2 from above
            if not isinstance(control_variable_symbol.pascal_type, pascaltypes.OrdinalType):
                error_str = "'For' statements require control variables to be of ordinal type. "
                error_str += "Variable '{}' is of type '{}'".format(control_variable_token.value,
                                                                    control_variable_symbol.pascal_type.identifier)
                raise TACException(compiler_error_str(error_str, control_variable_token))

            if not ast.nearest_symbol_table().are_compatible(control_variable_symbol.pascal_type.identifier,
                                                             temp1.pascal_type.identifier):
                error_str = "Type {} not compatible with type {} in 'for' statement"
                error_str = error_str.format(control_variable_symbol.pascal_type.identifier,
                                             temp1.pascal_type.identifier)
                raise TACException(compiler_error_str(error_str, assignment_ast.children[1].token))

            if not ast.nearest_symbol_table().are_compatible(control_variable_symbol.pascal_type.identifier,
                                                             temp2.pascal_type.identifier):
                error_str = "Type {} not compatible with type {} in 'for' statement"
                error_str = error_str.format(control_variable_symbol.pascal_type.identifier,
                                             temp2.pascal_type.identifier)
                raise TACException(compiler_error_str(error_str, to_or_downto_ast.children[0].token))

            # rule 3 will be a runtime check

            # Enforce rule 4 from above
            self.validate_control_variable_not_threatened(control_variable_token.value, body_ast)

            # finish assembling the TAC
            # TODO - refactor process_ast_conditional_statement and the while from below so we don't have
            # to be repetitive

            if to_or_downto_ast.token.token_type == TokenType.TO:
                system_function_label = Label("_SUCC_ORDINAL")
                compare_operator = TACOperator.LESS_EQUAL
            else:
                system_function_label = Label("_PRED_ORDINAL")
                compare_operator = TACOperator.GREATER_EQUAL

            if_statement_is_done_label = self.get_label()
            self.add_node(TACCommentNode("If boolean_expression_symbol is true, we execute the body once."))
            if_condition_symbol = Symbol(self.get_temporary(), assignment_ast.children[1].token.location,
                                         pascaltypes.BooleanType())
            self.symbol_table.add(if_condition_symbol)
            self.add_node(TACBinaryNode(if_condition_symbol, compare_operator, temp1, temp2))
            self.add_node(TACIFZNode(if_condition_symbol, if_statement_is_done_label))
            self.add_node(TACUnaryNode(control_variable_symbol, TACOperator.ASSIGN, temp1))
            self.process_ast(body_ast)
            while_start_label = self.get_label()
            self.add_node(TACCommentNode("The for statement now becomes a while statement"))
            self.add_node(TACLabelNode(while_start_label))
            while_condition_symbol = Symbol(self.get_temporary(), to_or_downto_ast.children[0].token.location,
                                            pascaltypes.BooleanType())
            self.symbol_table.add(while_condition_symbol)
            self.add_node(TACBinaryNode(while_condition_symbol, TACOperator.NOT_EQUAL, control_variable_symbol, temp2))
            self.add_node(TACIFZNode(while_condition_symbol, if_statement_is_done_label))
            self.add_node(TACParamNode(control_variable_symbol))
            self.add_node(TACCallSystemFunctionNode(system_function_label, 1, control_variable_symbol))
            self.process_ast(body_ast)
            self.add_node(TACGotoNode(while_start_label))
            self.add_node(TACLabelNode(if_statement_is_done_label))
            # 6.8.3.9 - "After a for-statement is executed,
            # other than being left by a goto-statement, the control-variable shall be undefined"
            control_variable_symbol.is_assigned_to = False

        elif token.token_type == TokenType.WHILE:
            assert len(ast.children) == 2, "TACBlock.process_ast_repetitive_statement - While ASTs must have 2 children"
            while_start_label = self.get_label()
            while_done_label = self.get_label()

            self.add_node(TACLabelNode(while_start_label))
            boolean_expression_symbol = self.process_ast(ast.children[0])
            if boolean_expression_symbol is None or not isinstance(boolean_expression_symbol.pascal_type,
                                                                   pascaltypes.BooleanType):
                raise TACException(
                    compiler_error_str("While statements must be followed by Boolean Expressions: ", token))
            self.add_node(TACIFZNode(boolean_expression_symbol, while_done_label))
            self.process_ast(ast.children[1])
            self.add_node(TACGotoNode(while_start_label))
            self.add_node(TACLabelNode(while_done_label))
        else:  # TokenType.REPEAT
            repeat_start_label = self.get_label()
            self.add_node(TACLabelNode(repeat_start_label))
            for child in ast.children[:-1]:
                self.process_ast(child)
            # the condition for a repeat is the last child
            boolean_expression_symbol = self.process_ast(ast.children[-1])
            self.add_node(TACIFZNode(boolean_expression_symbol, repeat_start_label))

    def process_ast_input_output(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.INPUT, TokenType.OUTPUT)
        return self.symbol_table.fetch(ast.token.value)

    def process_ast_identifier(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type == TokenType.IDENTIFIER

        # undefined identifiers are caught upstream
        assert self.symbol_table.exists_anywhere(ast.token.value)
        tac_symbol = self.symbol_table.fetch(ast.token.value)
        if isinstance(tac_symbol, FunctionResultVariableSymbol):
            # need to see if it's really the result of a function, or a recursive function call
            # if it is the result of a function, the parent will be an assign and this will be the left child
            if ast.parent.token.token_type == TokenType.ASSIGNMENT and ast.parent.children[0] == ast:
                pass
            else:
                # we know it is a function call, so get the activation symbol, which is stored in the parent
                tac_symbol = self.symbol_table.parent.fetch(ast.token.value)
        if isinstance(tac_symbol, ConstantSymbol):
            # optimization for integers - we can just return the literal itself instead of an assignment to
            # a local symbol.
            if isinstance(tac_symbol.pascal_type, pascaltypes.IntegerType):
                return IntegerLiteral(tac_symbol.value, ast.token.location)
            else:
                return_symbol = ConstantSymbol(self.get_temporary(), ast.token.location, tac_symbol.pascal_type,
                                               tac_symbol.value)
                self.symbol_table.add(return_symbol)
                if isinstance(tac_symbol.pascal_type, pascaltypes.BooleanType):
                    assert tac_symbol.value.lower() in ("true", "false")
                    if tac_symbol.value.lower() == 'true':
                        token_value = "1"
                    else:
                        token_value = "0"
                    return_literal = BooleanLiteral(token_value, ast.token.location)
                elif isinstance(tac_symbol.pascal_type, pascaltypes.StringLiteralType):
                    return_literal = StringLiteral(tac_symbol.value, ast.token.location)
                elif isinstance(tac_symbol.pascal_type, pascaltypes.CharacterType):
                    return_literal = CharacterLiteral(tac_symbol.value, ast.token.location)
                elif isinstance(tac_symbol.pascal_type, pascaltypes.RealType):
                    return_literal = RealLiteral(tac_symbol.value, ast.token.location)
                else:
                    assert isinstance(tac_symbol.pascal_type, pascaltypes.EnumeratedType)
                    return_literal = IntegerLiteral(str(tac_symbol.pascal_type.position(tac_symbol.value)),
                                                    ast.token.location)
                self.add_node(TACUnaryLiteralNode(return_symbol, TACOperator.ASSIGN, return_literal))
        elif isinstance(tac_symbol, pascaltypes.EnumeratedTypeValue):
            # need to return a symbol.
            # TODO - return the enumerated type value so that we can make it a literal here instead of a symbol
            # assign.  Cannot return an IntegerLiteral here because then it will not assign properly to values
            # of the enumerated type.  Likely need an EnumeratedTypeLiteral

            return_literal = Symbol(self.get_temporary(), ast.token.location,
                                    self.symbol_table.fetch(tac_symbol.type_identifier))
            self.symbol_table.add(return_literal)
            comment = "Convert literal '{}' to integer value {}".format(tac_symbol.identifier, tac_symbol.value)
            self.add_node(TACCommentNode(comment))
            self.add_node(TACUnaryLiteralNode(return_literal, TACOperator.ASSIGN,
                                              IntegerLiteral(str(tac_symbol.value), ast.token.location)))
            return return_literal
        elif not isinstance(tac_symbol, ActivationSymbol):
            # just return the identifier itself
            return_symbol = tac_symbol
        else:
            # Invoke the procedure or function.  If it is a Procedure, we will return
            # nothing.  If a function, we will return a symbol that contains the return value of the
            # function.
            assert isinstance(tac_symbol, ActivationSymbol)  # removes PyCharm errors
            # children of the AST node are the parameters to the proc/func.  Validate count is correct
            if len(ast.children) != len(tac_symbol.parameter_list):
                error_str = "{} expected {} parameters, but {} provided"
                error_str = error_str.format(ast.token.value, len(tac_symbol.parameter_list.parameter_list),
                                             len(ast.children))
                raise TACException(compiler_error_str(error_str, ast.token))

            for i in range(0, len(ast.children)):
                child = ast.children[i]
                child_symbol = self.process_ast(child)
                assert child_symbol is not None, "TACBlock.process_ast_identifier: parameter has None value"

                if tac_symbol.parameter_list[i].is_by_ref:
                    # 6.6.3.3 of the ISO Standard states that if the formal parameter is a variable
                    # parameter, then the actual parameter must be the same type as the formal parameter
                    # and the actual parameter must be a variable access, meaning it cannot be a literal
                    # or the output of a function.
                    if not isinstance(child_symbol, VariableSymbol):
                        error_str = "Must pass in variable for parameter {} of {}()".format(
                            tac_symbol.parameter_list[i].symbol.name, tac_symbol.name)
                        raise TACException(compiler_error_str(error_str, child.token))

                    # For variable parameters, the actual parameter must have same type as the formal parameter
                    if not ast.nearest_symbol_table().are_same_type(child_symbol.pascal_type.identifier,
                                                                    tac_symbol.parameter_list[
                                                                        i].symbol.pascal_type.identifier):
                        error_str = "Type Mismatch - parameter {} of {}() must be type {}"
                        error_str = error_str.format(tac_symbol.parameter_list[i].symbol.name, tac_symbol.name,
                                                     str(tac_symbol.parameter_list[i].symbol.pascal_type.identifier))
                        raise TACException(compiler_error_str(error_str, child.token))
                else:
                    # For value parameters, the actual parameter must be assignment compatible with the formal
                    # parameter
                    if isinstance(child_symbol, ConstantSymbol):
                        optional_constant_value = child_symbol.value
                    else:
                        optional_constant_value = None

                    if not ast.nearest_symbol_table().are_assignment_compatible(
                            tac_symbol.parameter_list[i].symbol.pascal_type.identifier,
                            child_symbol.pascal_type.identifier,
                            optional_constant_value):
                        error_str = "Error D.7: Type Mismatch - {} is not assignment compatible with parameter "
                        error_str += "{} of {}()"
                        error_str = error_str.format(str(child_symbol.pascal_type.identifier),
                                                     tac_symbol.parameter_list[i].symbol.name, tac_symbol.name)
                        raise TACException(compiler_error_str(error_str, child.token))

                if isinstance(child_symbol.pascal_type, pascaltypes.IntegerType) and \
                        isinstance(tac_symbol.parameter_list[i].symbol.pascal_type, pascaltypes.RealType):
                    self.add_node(TACParamNode(self.process_symbol_int_to_real(child_symbol)))
                else:
                    self.add_node(TACParamNode(child_symbol))

            if tac_symbol.result_type is not None:
                # means it is a function
                return_symbol = Symbol(self.get_temporary(), ast.token.location, tac_symbol.result_type)
                self.symbol_table.add(return_symbol)
            else:
                # procedures return nothing
                return_symbol = None
            self.add_node(TACCallFunctionNode(tac_symbol.label, tac_symbol.name, len(ast.children), return_symbol))

        return return_symbol

    def process_ast_integer_literal(self, ast):
        # This function is static (no references to self) but because of what it does, I have it included in the
        # object instead of a standalone helper function.
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.UNSIGNED_INT, TokenType.SIGNED_INT, TokenType.MAXINT)

        if ast.token.token_type in (TokenType.UNSIGNED_INT, TokenType.SIGNED_INT):
            return_literal = IntegerLiteral(ast.token.value, ast.token.location)
        else:
            assert ast.token.token_type == TokenType.MAXINT
            return_literal = IntegerLiteral(pascaltypes.MAXINT_AS_STRING, ast.token.location)
        return return_literal

    def process_ast_real_literal(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.SIGNED_REAL, TokenType.UNSIGNED_REAL)

        literal = RealLiteral(ast.token.value, ast.token.location)
        return_symbol = ConstantSymbol(self.get_temporary(), ast.token.location, pascaltypes.RealType(),
                                       ast.token.value)
        self.symbol_table.add(return_symbol)
        self.add_node(TACUnaryLiteralNode(return_symbol, TACOperator.ASSIGN, literal))
        return return_symbol

    def process_ast_boolean_literal(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.TRUE, TokenType.FALSE)

        return_symbol = ConstantSymbol(self.get_temporary(), ast.token.location, pascaltypes.BooleanType(),
                                       ast.token.value)
        self.symbol_table.add(return_symbol)
        if ast.token.token_type == TokenType.TRUE:
            token_value = "1"  # 6.4.2.2 of ISO standard - Booleans are stored as 0 or 1 in memory
        else:
            token_value = "0"
        self.add_node(
            TACUnaryLiteralNode(return_symbol, TACOperator.ASSIGN, BooleanLiteral(token_value, ast.token.location)))
        return return_symbol

    def process_ast_character_string(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type == TokenType.CHARSTRING

        # string of length 1 is a character.  String of any other length is a string literal
        if len(ast.token.value) != 1:
            literal_type = pascaltypes.StringLiteralType()
            lit = StringLiteral(ast.token.value, ast.token.location)
        else:
            literal_type = pascaltypes.CharacterType()
            lit = CharacterLiteral(ast.token.value, ast.token.location)

        return_symbol = ConstantSymbol(self.get_temporary(), ast.token.location, literal_type, ast.token.value)
        self.symbol_table.add(return_symbol)
        self.add_node(TACUnaryLiteralNode(return_symbol, TACOperator.ASSIGN, lit))
        return return_symbol

    def process_ast_array(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type == TokenType.LEFT_BRACKET
        assert len(ast.children) == 2, "TACBlock.process_ast_array - Array ASTs must have 2 children."

        '''
        Core Logic:
            Step 1 - resolve the left_value.  It will either be a symbol with a pascal_type of an array, or a 
            pointer, that points to the type of an array.
            
            Step 2 - create a symbol that is a pointer that points to the left_value array's component type.
            If the left_value is an array symbol, set left_value to the address of the array.  If the left_value is 
            already a pointer, then set this symbol equal to the left_value.
            
            Step 3 - grab the result of the index expression
            
            Step 4 - compute the size of the component type of the array.  Take the result of step 3,
            subtract the index minimum of the array from that, and then multiply it by the size of the
            component type.  If the result of step 3 is a literal, we can do the math in the compiler.
            If the result of step 3 is a symbol, then we need to do the math at runtime.
            
            Step 5 - add the number of bytes result from step 4, add that to the address of the pointer
            in step 2, and store that result in a symbol.  The pascal_type for the symbol should equal
            a pointer to the component type for the array.  Return this symbol.
        '''

        step1 = self.process_ast(ast.children[0])
        assert isinstance(step1.pascal_type, pascaltypes.ArrayType) or \
               (isinstance(step1.pascal_type, pascaltypes.PointerType) and
                isinstance(step1.pascal_type.points_to_type, pascaltypes.ArrayType))

        if isinstance(step1.pascal_type, pascaltypes.ArrayType):
            array_type = step1.pascal_type
            assignment_operator = TACOperator.ASSIGN_ADDRESS_OF
        else:
            array_type = step1.pascal_type.points_to_type
            assert isinstance(array_type, pascaltypes.ArrayType)
            assignment_operator = TACOperator.ASSIGN

        component_type = array_type.component_type
        indextype = array_type.index_type

        step2 = Symbol(self.get_temporary(), step1.location, component_type.get_pointer_to())
        self.symbol_table.add(step2)
        self.add_node(TACUnaryNode(step2, assignment_operator, step1))

        step3 = self.dereference_if_needed(self.process_ast(ast.children[1]), ast.children[1].token)

        # the type of the index expression must be assignment compatible with the index type
        # (Cooper p.115)
        if not self.symbol_table.are_assignment_compatible(indextype.identifier, step3.pascal_type.identifier):
            # Error D.1 comes from 6.5.3.2 of the ISO standard
            raise TACException(compiler_error_str("Error D.1: Incorrect type for array index", ast.children[1].token))

        # logic here - take result of (step 3 minus the minimum index) and multiply by the component size.
        # add that to the result of step 2.

        # TODO - if the array is an enumerated type (and possibly an ordinal type like char) it will not have
        # a subrange.
        if isinstance(indextype, pascaltypes.SubrangeType):
            range_minimum = indextype.range_min_int
            range_maximum = indextype.range_max_int
        else:
            assert isinstance(indextype, pascaltypes.OrdinalType)
            if isinstance(indextype, pascaltypes.IntegerType):
                error_str = compiler_error_str("Cannot have an array with index range 'integer'", ast.token)
                raise TACException(error_str)
            range_minimum = indextype.position(indextype.min_item())
            range_maximum = indextype.position(indextype.max_item())

        if isinstance(step3, IntegerLiteral):
            # we can do the math in the compiler
            if int(step3.value) < range_minimum or int(step3.value) > range_maximum:
                error_str = compiler_error_str("Array Index '{}' out of range".format(step3.value),
                                               ast.children[1].token)
                raise TACException(error_str)

            index_position = (int(step3.value) - range_minimum)
            numbytes = index_position * component_type.size
            step4 = IntegerLiteral(str(numbytes), step1.location)
        else:
            step4a = Symbol(self.get_temporary(), step1.location, pascaltypes.IntegerType())
            index_minimum_literal = IntegerLiteral(str(range_minimum), step1.location)
            size_literal = IntegerLiteral(str(component_type.size), step1.location)
            self.symbol_table.add(step4a)
            self.add_node(TACBinaryNode(step4a, TACOperator.SUBTRACT, step3, index_minimum_literal))
            step4 = Symbol(self.get_temporary(), step1.location, pascaltypes.IntegerType())
            self.symbol_table.add(step4)
            self.add_node(TACBinaryNode(step4, TACOperator.MULTIPLY, step4a, size_literal))

        step5 = Symbol(self.get_temporary(), step1.location, step2.pascal_type)
        self.symbol_table.add(step5)

        self.add_node(TACBinaryNodeWithBoundsCheck(step5, TACOperator.ADD, step2, step4, 0, array_type.size - 1))
        return step5

    def process_ast_assignment(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type == TokenType.ASSIGNMENT
        assert len(ast.children) == 2, "TACBlock.process_ast_assignment: Assignment ASTs must have 2 children."

        left_value_symbol = self.process_ast(ast.children[0])
        if isinstance(left_value_symbol.pascal_type, pascaltypes.PointerType):
            left_value_reference_type = left_value_symbol.pascal_type.points_to_type
            assignment_operator = TACOperator.ASSIGN_TO_DEREFERENCE
        else:
            left_value_reference_type = left_value_symbol.pascal_type
            assignment_operator = TACOperator.ASSIGN

        # assigning to constant is caught upstream
        assert not isinstance(left_value_symbol,
                              ConstantSymbol), "TACBlock.process_ast_assignment: attempted to assign to constant"

        right_value_symbol = self.dereference_if_needed(self.process_ast(ast.children[1]), ast.children[1].token)

        if isinstance(right_value_symbol, pascaltypes.EnumeratedTypeValue):
            # Note 2025-11-09 - unsure how to execute this block, may need to assert that we do not have
            # an enumerated type as the right value
            comment = "Convert literal {} to integer value {}".format(right_value_symbol.identifier,
                                                                      right_value_symbol.value)
            self.add_node(TACCommentNode(comment))
            self.add_node(TACUnaryLiteralNode(left_value_symbol, TACOperator.ASSIGN,
                                              IntegerLiteral(str(right_value_symbol.value),
                                                             ast.children[1].token.location)))
        else:
            if isinstance(right_value_symbol, ConstantSymbol) or isinstance(right_value_symbol, IntegerLiteral):
                right_value = right_value_symbol.value
            else:
                right_value = None

            if not ast.nearest_symbol_table().are_assignment_compatible(left_value_reference_type.identifier,
                                                                        right_value_symbol.pascal_type.identifier,
                                                                        right_value):
                if right_value is not None:
                    error_str = "Cannot assign value '{}' of type {} to type {}"
                    if isinstance(right_value_symbol.pascal_type, pascaltypes.OrdinalType):
                        # the error in 6.8.2.2 is specific to ordinal types.
                        error_str = "Error D.49: " + error_str
                    error_str = error_str.format(right_value, right_value_symbol.pascal_type.identifier,
                                                 left_value_reference_type.identifier)
                else:
                    error_str = "Cannot assign {} type to {}".format(right_value_symbol.pascal_type.identifier,
                                                                     left_value_reference_type.identifier)
                raise TACException(compiler_error_str(error_str, ast.children[1].token))
            if isinstance(left_value_reference_type, pascaltypes.RealType) and \
                    isinstance(right_value_symbol.pascal_type, pascaltypes.IntegerType):
                new_right_value_symbol = self.process_symbol_int_to_real(right_value_symbol)
            else:
                new_right_value_symbol = right_value_symbol

            left_value_symbol.is_assigned_to = True

            if isinstance(new_right_value_symbol, Literal):
                self.add_node(TACUnaryLiteralNode(left_value_symbol, assignment_operator, new_right_value_symbol))
            else:
                self.add_node(TACUnaryNode(left_value_symbol, assignment_operator, new_right_value_symbol))
        return left_value_symbol

    def process_symbol_int_to_real(self, integer_symbol):
        # integer_symbol is a symbol of integer type.  Adds a node that does the conversion and returns a symbol
        # that represents the converted integer.
        assert isinstance(integer_symbol, Symbol) or isinstance(integer_symbol, IntegerLiteral)
        if isinstance(integer_symbol, Symbol):
            assert isinstance(integer_symbol.pascal_type, pascaltypes.IntegerType)
        real_symbol = Symbol(self.get_temporary(), integer_symbol.location, pascaltypes.RealType())
        self.symbol_table.add(real_symbol)
        if isinstance(integer_symbol, Symbol):
            self.add_node(TACUnaryNode(real_symbol, TACOperator.INT_TO_REAL, integer_symbol))
        else:
            self.add_node(TACUnaryLiteralNode(real_symbol, TACOperator.INT_TO_REAL, integer_symbol))
        return real_symbol

    def process_ast_arithmetic_operator(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.MULTIPLY, TokenType.PLUS, TokenType.MINUS, TokenType.DIVIDE,
                                        TokenType.INTEGER_DIV, TokenType.MOD)
        assert len(ast.children) == 2

        tac_operator = map_token_type_to_tac_operator(ast.token.token_type)
        child0 = self.dereference_if_needed(self.process_ast(ast.children[0]), ast.children[0].token)
        child1 = self.dereference_if_needed(self.process_ast(ast.children[1]), ast.children[1].token)

        if isinstance(child0.pascal_type, pascaltypes.BooleanType) or \
                isinstance(child1.pascal_type, pascaltypes.BooleanType):
            raise TACException(compiler_error_str("Cannot use boolean type with math operators", ast.token))

        if ast.token.token_type in (TokenType.INTEGER_DIV, TokenType.MOD) and \
                (isinstance(child0.pascal_type, pascaltypes.RealType) or
                 isinstance(child1.pascal_type, pascaltypes.RealType)):
            raise TACException(compiler_error_str("Cannot use integer division with real values.", ast.token))

        # The addition, subtraction, multiplication operators can take integers or reals, and return
        # integer if both operands are integers, or a real if one or both operands are reals.  The
        # division operator returns a real even if both operands are integers
        if isinstance(child0.pascal_type, pascaltypes.RealType) or \
                isinstance(child1.pascal_type, pascaltypes.RealType) or \
                tac_operator == TACOperator.DIVIDE:

            # 6.7.2.1 of the ISO Standard states that if either operand of addition, subtraction, or multiplication
            # are real-type, then the result will also be real-type.  Similarly, if the "/" operator is used,
            # even if both operands are integer-type, the result is real-type.  Cooper states on p.31 that
            # "[t]his means that integer operands are sometimes coerced into being reals; i.e. they are temporarily
            # treated as values of type real."
            if isinstance(child0.pascal_type, pascaltypes.IntegerType):
                new_child0 = self.process_symbol_int_to_real(child0)
            else:
                new_child0 = child0

            if isinstance(child1.pascal_type, pascaltypes.IntegerType):
                new_child1 = self.process_symbol_int_to_real(child1)
            else:
                new_child1 = child1

            return_symbol = Symbol(self.get_temporary(), ast.token.location, pascaltypes.RealType())
            self.symbol_table.add(return_symbol)
            self.add_node(TACBinaryNode(return_symbol, tac_operator, new_child0, new_child1))
        else:
            return_symbol = Symbol(self.get_temporary(), ast.token.location, pascaltypes.IntegerType())
            self.symbol_table.add(return_symbol)
            self.add_node(TACBinaryNode(return_symbol, tac_operator, child0, child1))
        return return_symbol

    def process_ast_relational_operator(self, ast):
        assert isinstance(ast, AST)
        assert is_relational_operator(ast.token.token_type)

        tac_operator = map_token_type_to_tac_operator(ast.token.token_type)
        child0 = self.dereference_if_needed(self.process_ast(ast.children[0]), ast.children[0].token)
        child1 = self.dereference_if_needed(self.process_ast(ast.children[1]), ast.children[1].token)

        # 6.7.2.5 of the ISO standard says that the operands of relational operators shall be of compatible
        # types, or one operand shall be of real-type and the other of integer-type.  Table 6, has
        # simple-types, pointer-types, and string-types allowed in the comparisons.

        # special case for string literals - symbol_table.are_compatible() just looks at the identifiers,
        # which works fine for every time other than string literals doing relational comparisons.  For
        # string literals we need to look at the length to know if they are compatible.

        if not self.symbol_table.are_compatible(child0.pascal_type.identifier, child1.pascal_type.identifier, child0,
                                                child1):
            if isinstance(child0.pascal_type, pascaltypes.IntegerType) and isinstance(child1.pascal_type,
                                                                                      pascaltypes.RealType):
                pass
            elif isinstance(child1.pascal_type, pascaltypes.IntegerType) and isinstance(child0.pascal_type,
                                                                                        pascaltypes.RealType):
                pass
            elif isinstance(child0.pascal_type, pascaltypes.BooleanType) or isinstance(child1.pascal_type,
                                                                                       pascaltypes.BooleanType):
                raise TACException(compiler_error_str("Cannot compare Boolean to non-Boolean", ast.token))
            else:
                error_str = "Cannot compare types '{}' and '{}' with relational operator"
                error_str = error_str.format(child0.pascal_type.identifier, child1.pascal_type.identifier)
                raise TACException(compiler_error_str(error_str, ast.token))

        if isinstance(child0.pascal_type, pascaltypes.IntegerType) and isinstance(child1.pascal_type,
                                                                                  pascaltypes.RealType):
            new_child0 = self.process_symbol_int_to_real(child0)
        else:
            new_child0 = child0
        if isinstance(child1.pascal_type, pascaltypes.IntegerType) and isinstance(child0.pascal_type,
                                                                                  pascaltypes.RealType):
            new_child1 = self.process_symbol_int_to_real(child1)
        else:
            new_child1 = child1

        ret = Symbol(self.get_temporary(), ast.token.location, pascaltypes.BooleanType())
        self.symbol_table.add(ret)
        self.add_node(TACBinaryNode(ret, tac_operator, new_child0, new_child1))
        return ret

    def process_ast_boolean_operator(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.AND, TokenType.OR, TokenType.NOT)

        tac_operator = map_token_type_to_tac_operator(ast.token.token_type)

        if ast.token.token_type in (TokenType.AND, TokenType.OR):
            child0 = self.dereference_if_needed(self.process_ast(ast.children[0]), ast.children[0].token)
            child1 = self.dereference_if_needed(self.process_ast(ast.children[1]), ast.children[1].token)
            if not isinstance(child0.pascal_type, pascaltypes.BooleanType) or \
                    not isinstance(child1.pascal_type, pascaltypes.BooleanType):
                error_str = "Both arguments to operator '{}' must be Boolean type".format(ast.token.value)
                raise TACException(compiler_error_str(error_str, ast.token))
            return_symbol = Symbol(self.get_temporary(), ast.token.location, pascaltypes.BooleanType())
            self.symbol_table.add(return_symbol)
            self.add_node(TACBinaryNode(return_symbol, tac_operator, child0, child1))
        else:  # token.token_type == TokenType.NOT
            child = self.dereference_if_needed(self.process_ast(ast.children[0]), ast.children[0].token)
            if not isinstance(child.pascal_type, pascaltypes.BooleanType):
                raise TACException(
                    compiler_error_str("Operator 'not' can only be applied to Boolean factors", ast.token))
            return_symbol = Symbol(self.get_temporary(), ast.token.location, pascaltypes.BooleanType())
            self.symbol_table.add(return_symbol)
            self.add_node(TACUnaryNode(return_symbol, tac_operator, child))
        return return_symbol

    def process_ast(self, ast):
        """ returns the Symbol of a temporary that holds the result of this computation, or None """

        assert isinstance(ast, AST)
        if ast.comment != "":
            self.add_node(TACCommentNode(ast.comment))

        ast_token_type = ast.token.token_type

        # Begin statements, Procedure/Function declarations, Output, Conditionals, and Repetitive statements
        # do not return anything.  Identifiers generally do, unless they are procedure calls.  Everything else
        # returns a symbol.

        return_symbol = None

        if ast_token_type == TokenType.BEGIN:
            self.process_ast_begin(ast)
        elif ast_token_type in (TokenType.PROCEDURE, TokenType.FUNCTION):
            self.process_ast_procedure_or_function(ast)
        elif ast_token_type in (TokenType.RESET, TokenType.REWRITE):
            self.process_ast_file_procedure(ast)
        elif ast_token_type in (TokenType.WRITE, TokenType.WRITELN):
            self.process_ast_write(ast)
        elif ast_token_type == TokenType.GOTO:
            self.process_ast_goto(ast)
        elif ast_token_type == TokenType.IF:
            self.process_ast_conditional_statement(ast)
        elif ast_token_type in (TokenType.WHILE, TokenType.REPEAT, TokenType.FOR):
            self.process_ast_repetitive_statement(ast)
        elif is_iso_required_function(ast_token_type):
            return_symbol = self.process_ast_iso_required_function(ast)
        elif ast_token_type == TokenType.LEFT_BRACKET:
            return_symbol = self.process_ast_array(ast)
        elif ast_token_type == TokenType.ASSIGNMENT:
            return_symbol = self.process_ast_assignment(ast)
        elif ast_token_type == TokenType.IDENTIFIER:
            return_symbol = self.process_ast_identifier(ast)
        elif ast_token_type in (TokenType.INPUT, TokenType.OUTPUT):
            return_symbol = self.process_ast_input_output(ast)
        elif ast_token_type in (TokenType.UNSIGNED_INT, TokenType.SIGNED_INT, TokenType.MAXINT):
            return_symbol = self.process_ast_integer_literal(ast)
        elif ast_token_type in (TokenType.UNSIGNED_REAL, TokenType.SIGNED_REAL):
            return_symbol = self.process_ast_real_literal(ast)
        elif ast_token_type in [TokenType.TRUE, TokenType.FALSE]:
            return_symbol = self.process_ast_boolean_literal(ast)
        elif ast_token_type == TokenType.CHARSTRING:
            return_symbol = self.process_ast_character_string(ast)
        elif ast_token_type in (TokenType.MULTIPLY, TokenType.PLUS, TokenType.MINUS, TokenType.DIVIDE,
                                TokenType.INTEGER_DIV, TokenType.MOD):
            return_symbol = self.process_ast_arithmetic_operator(ast)
        elif is_relational_operator(ast_token_type):
            return_symbol = self.process_ast_relational_operator(ast)
        elif ast_token_type in (TokenType.AND, TokenType.OR, TokenType.NOT):
            return_symbol = self.process_ast_boolean_operator(ast)
        elif ast_token_type == TokenType.EMPTY_TOKEN:
            self.add_node(TACNoOpNode())
        else:  # pragma: no cover
            raise TACException(
                compiler_error_str("TACBlock.process_ast - cannot process token:".format(str(ast.token)), ast.token))

        assert return_symbol is None or isinstance(return_symbol, Symbol) or isinstance(return_symbol, IntegerLiteral)
        return return_symbol


class TACGenerator:
    def __init__(self, literal_table):
        assert isinstance(literal_table, LiteralTable)
        self.tac_blocks_list = []
        self.next_label = 0
        self.next_temporary = 0
        self.global_symbol_table = SymbolTable()
        self.global_literal_table = deepcopy(literal_table)
        self.warnings_list = []

    def add_block(self, block):
        assert isinstance(block, TACBlock)
        self.tac_blocks_list.append(block)

    def generate_block(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.BEGIN, TokenType.PROCEDURE, TokenType.FUNCTION)
        # process the main begin
        if ast.token.token_type == TokenType.BEGIN:
            new_block = TACBlock(True, self)
        else:
            new_block = TACBlock(False, self)
            new_block.symbol_table = deepcopy(ast.symbol_table)
        new_block.symbol_table.parent = self.global_symbol_table
        new_block.process_ast(ast)
        return new_block

    def generate(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type == TokenType.PROGRAM
        self.global_symbol_table = deepcopy(ast.symbol_table)

        for child in ast.children:
            self.add_block(self.generate_block(child))
        # insure there is exactly one main block
        main_block_count = 0
        for block in self.tac_blocks_list:
            if block.is_main:
                main_block_count += 1
        assert (main_block_count == 1), \
            "TACGenerator.generate created {} main blocks instead of 1".format(str(main_block_count))

    def get_label(self, label_suffix=""):
        # labels begin with _TAC_L so that they do not collide with the labels generated in AssemblyGenerator.
        label = Label("_TAC_L{}_{}".format(str(self.next_label), label_suffix))
        self.next_label += 1
        return label

    def get_temporary(self):
        temporary = "_T" + str(self.next_temporary)
        self.next_temporary += 1
        return temporary

    def print_blocks(self):  # pragma: no cover
        for block in self.tac_blocks_list:
            if block.is_main:
                print("_MAIN:")
            block.print_nodes()
