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

        After calling a procedure or function, there must be a "clearparam" statement.  This will be used if
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
    return "_{}{}".format(str(token.token_type).upper(), type_str.upper())


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
        return self.generator.getlabel(label_suffix)

    def get_temporary(self):
        return self.generator.gettemporary()

    def add_node(self, node):
        assert isinstance(node, TACNode)
        self.tacnodes.append(node)

    def print_nodes(self):  # pragma: no cover
        for node in self.tacnodes:
            print(str(node))

    def process_ast_begin(self, ast):
        assert isinstance(ast, AST)
        for child in ast.children:
            self.processast(child)

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
                            self.generator.warningslist.append(warning_str)
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
            retvalisassigned_variablename = '_{}_isassigned'.format(procedure_name)
            retvalisassignedsym = VariableSymbol(retvalisassigned_variablename, token.location, pascaltypes.BooleanType())
            self.symbol_table.add(retvalisassignedsym)
            ast.symbol_table.add(retvalisassignedsym)

            # create an AST that initializes this variable to False, and make that the first statement executed
            # in the current AST.
            retvalisassigned_initialize_ast = AST(Token(TokenType.ASSIGNMENT, None, ":="), ast,
                                                  "initialize {} to false".format(retvalisassigned_variablename))
            retvalisassignedtoken = Token(TokenType.IDENTIFIER, token.location, retvalisassigned_variablename)
            falsetoken = Token(TokenType.FALSE, token.location, 'false')
            retvalisassigned_initialize_ast.children.append(AST(retvalisassignedtoken, retvalisassigned_initialize_ast))
            retvalisassigned_initialize_ast.children.append(AST(falsetoken, retvalisassigned_initialize_ast))
            # make this assignment become the first statement in the function
            ast.children[1].children.insert(0, retvalisassigned_initialize_ast)
            # debugprintast = AST(Token(TokenType.WRITELN, None, 'writeln'), ast, "Debug print {}".format(retvalisassigned_variablename))
            # debugprintast.children.append(
            #     AST(Token(TokenType.IDENTIFIER, None, retvalisassigned_variablename), ast))
            # ast.children[1].children.insert(1, debugprintast)

            # recursively iterate through the children of the current AST, starting with the one following the
            # assignment we just inserted, and identify any assignments to the retval.  This requires matching on
            # the symbols themselves, not the names, as function declared inside a function could reuse a name.
            retvalsym = ast.symbol_table.fetch(procedure_name)
            retvaleverset = False
            for child in ast.children[1].children[1:]:
                if self.track_function_return_value_assignments(retvalsym, retvalisassignedsym, child):
                    retvaleverset = True

            # check if the return value is assigned to at least once in the ast.
            if not retvaleverset:
                error_str = 'Error D.48: Function {} must have a return value'.format(procedure_name)
                raise TACException(compiler_error_str(error_str, token))

            # now we need to test that the returnvalue was assigned
            child = ast.children[1]  # only needed to anchor the locations for the ASTs I'm creating below.
            testast = AST(Token(TokenType.IF, child.token.location, 'if'), ast,
                          'if {} = False, then error'.format(retvalisassigned_variablename))
            conditionast = AST(Token(TokenType.EQUALS, child.token.location, '='), testast,
                               'if {} = false'.format(retvalisassigned_variablename))
            # I could probably reuse these tokens, but I'm very conservative
            conditionast.children.append(AST(deepcopy(retvalisassignedtoken), conditionast))
            conditionast.children.append(AST(deepcopy(falsetoken), conditionast))
            testast.children.append(conditionast)

            gotoast = AST(Token(TokenType.GOTO, child.token.location, 'goto'), testast,
                          'goto _PASCAL_NORETURNVAL_ERROR')
            labelast = AST(Token(TokenType.LABEL, child.token.location, '_PASCAL_NORETURNVAL_ERROR'), gotoast,
                           '_PASCAL_NORETURNVAL_ERROR')
            gotoast.children.append(labelast)
            testast.children.append(gotoast)

            ast.children.append(testast)
        else:
            comment = "Procedure {}({})".format(procedure_name, str(self.parameter_list))
        self.add_node(TACLabelNode(activation_label, comment))

        for child in ast.children[1:]:
            self.processast(child)

        if token.token_type == TokenType.FUNCTION:
            self.add_node(TACFunctionReturnNode(self.symbol_table.fetch(procedure_name)))
        else:
            self.add_node(TACFunctionReturnNode(None))

    def processast_isorequiredfunction(self, ast):
        assert isinstance(ast, AST)
        assert is_iso_required_function(ast.token.token_type)

        tok = ast.token
        tmp = self.dereference_if_needed(self.processast(ast.children[0]), ast.children[0].token)
        lval = Symbol(self.get_temporary(), tok.location,
                      required_function_return_type(tok.token_type, tmp.pascal_type))
        self.symbol_table.add(lval)
        if required_function_accepts_ordinal(tok.token_type):
            if isinstance(tmp.pascal_type, pascaltypes.OrdinalType):
                self.add_node(TACParamNode(tmp))
                self.add_node(TACCallSystemFunctionNode(Label(map_token_to_system_function_name(tok, "O")), 1, lval))
            else:
                raise TACException(
                    compiler_error_str('Function {}() requires parameter of ordinal type'.format(tok.token_type), tok))

        elif required_function_accepts_integer_or_real(tok.token_type):
            if pascaltypes.is_integer_or_subrange_of_integer(tmp.pascal_type):
                self.add_node(TACParamNode(tmp))
                self.add_node(TACCallSystemFunctionNode(Label(map_token_to_system_function_name(tok, "I")), 1, lval))
            elif isinstance(tmp.pascal_type, pascaltypes.RealType):
                self.add_node(TACParamNode(tmp))
                self.add_node(TACCallSystemFunctionNode(Label(map_token_to_system_function_name(tok, "R")), 1, lval))
            else:
                raise TACException(compiler_error_str(
                    'Function {}() requires parameter of integer or real type'.format(tok.token_type), tok))
        elif required_function_accepts_integer(tok.token_type):
            if pascaltypes.is_integer_or_subrange_of_integer(tmp.pascal_type):
                self.add_node(TACParamNode(tmp))
                self.add_node(TACCallSystemFunctionNode(Label(map_token_to_system_function_name(tok, "I")), 1, lval))
            else:
                raise TACException(
                    compiler_error_str('Function {}() requires parameter of integer type'.format(tok.token_type), tok))
        else:
            assert required_function_accepts_real(tok.token_type)
            if isinstance(tmp.pascal_type, pascaltypes.IntegerType):
                tmp2 = self.process_sym_inttoreal(tmp)
                self.add_node(TACParamNode(tmp2))
                self.add_node(TACCallSystemFunctionNode(Label(map_token_to_system_function_name(tok, "R")), 1, lval))
            elif isinstance(tmp.pascal_type, pascaltypes.RealType):
                self.add_node(TACParamNode(tmp))
                self.add_node(TACCallSystemFunctionNode(Label(map_token_to_system_function_name(tok, "R")), 1, lval))
            else:
                raise TACException(
                    compiler_error_str('Function {}() requires parameter of real type'.format(tok.token_type), tok))
        return lval

    def process_write_parameter(self, outputfile, paramsym, writetoken):
        assert isinstance(paramsym, Symbol) or isinstance(paramsym, Literal)

        bt = paramsym.pascal_type

        # p.98 of Cooper states that the constants of enumerated ordinal types (pascaltypes.EnumeratedType)
        # "don't have external character representations, and can't be read or written to or from
        # textfiles - in particular, from the standard input and output."  It would be very easy to
        # display the string representation of the constant when trying to print it out, but we will
        # stick to Cooper for now.  The ISO standard is silent on the topic, per my reading.
        if isinstance(bt, pascaltypes.SubrangeType):
            bt = bt.host_type

        if not (isinstance(bt, pascaltypes.StringLiteralType) or isinstance(bt, pascaltypes.RealType) or
                isinstance(bt, pascaltypes.BooleanType) or isinstance(bt, pascaltypes.IntegerType) or
                isinstance(bt, pascaltypes.CharacterType) or
                bt.is_string_type()):
            # TODO - this error string is ugly, but when we have files and can write arbitrary types, this
            # logic will need to change anyway.
            error_str = "'{}' is of type that cannot be displayed by {}()".format(paramsym.name, writetoken.value)
            raise TACException(compiler_error_str(error_str, writetoken))

        self.add_node(TACParamNode(outputfile))
        self.add_node(TACParamNode(paramsym))
        if isinstance(bt, pascaltypes.StringLiteralType):
            self.add_node(TACCallSystemFunctionNode(Label("_WRITESL"), 2))
        elif isinstance(bt, pascaltypes.RealType):
            self.add_node(TACCallSystemFunctionNode(Label("_WRITER"), 2))
        elif isinstance(bt, pascaltypes.BooleanType):
            self.add_node(TACCallSystemFunctionNode(Label("_WRITEB"), 2))
        elif isinstance(bt, pascaltypes.IntegerType):
            self.add_node(TACCallSystemFunctionNode(Label("_WRITEI"), 2))
        elif bt.is_string_type():
            self.add_node(TACCallSystemFunctionNode(Label("_WRITEST"), 2))
        else:
            self.add_node(TACCallSystemFunctionNode(Label("_WRITEC"), 2))

    def processast_fileprocedure(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.RESET, TokenType.REWRITE)
        assert len(ast.children) == 1

        tok = ast.token
        paramsym = self.processast(ast.children[0])
        if not isinstance(paramsym.pascal_type, pascaltypes.FileType):
            error_str = "Function {}() requires parameter of file type".format(tok.token_type)
            raise TACException(compiler_error_str(error_str, tok))

        if paramsym.name in ("output", "input"):
            error_str = "Cannot call {}() on built-in textfile {}".format(tok.token_type, paramsym.value)
            raise TACException(compiler_error_str(error_str, tok))

        self.add_node(TACParamNode(paramsym))

        if not isinstance(paramsym.pascal_type, pascaltypes.TextFileType):
            suffix = "B"
        else:
            suffix = ""

        sysfuncname = "_" + tok.value.upper() + suffix
        self.add_node(TACCallSystemFunctionNode(Label(sysfuncname), 1))

    def processast_write(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.WRITE, TokenType.WRITELN)
        tok = ast.token

        outputfile = self.symbol_table.fetch("output")
        if len(ast.children) > 0:
            childsym = self.dereference_if_needed(self.processast(ast.children[0]), ast.children[0].token)
            if isinstance(childsym.pascal_type, pascaltypes.FileType):
                outputfile = childsym
            else:
                self.process_write_parameter(outputfile, childsym, tok)

        for child in ast.children[1:]:
            childsym = self.dereference_if_needed(self.processast(child), child.token)
            self.process_write_parameter(outputfile, childsym, tok)

        if tok.token_type == TokenType.WRITELN:
            self.add_node(TACParamNode(outputfile))
            self.add_node(TACCallSystemFunctionNode(Label("_WRITECRLF"), 1))

    def processast_conditionalstatement(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type == TokenType.IF
        assert len(ast.children) in [2, 3], "TACBlock.processast - IF ASTs must have 2 or 3 children."

        tok = ast.token
        labeldone = self.get_label()
        condition = self.processast(ast.children[0])
        if not isinstance(condition.pascal_type, pascaltypes.BooleanType):
            raise TACException(compiler_error_str("If statements must be followed by Boolean expressions", tok))

        if len(ast.children) == 2:
            self.add_node(TACIFZNode(condition, labeldone))
            self.processast(ast.children[1])
            self.add_node(TACLabelNode(labeldone))
        else:
            labelelse = self.get_label()
            self.add_node(TACIFZNode(condition, labelelse))
            self.processast(ast.children[1])
            self.add_node(TACGotoNode(labeldone))
            self.add_node(TACCommentNode("ELSE"))
            self.add_node(TACLabelNode(labelelse))
            self.processast(ast.children[2])
            self.add_node(TACLabelNode(labeldone))

    def validate_controlvariable_notthreatened(self, controlvariableidentifier, ast):
        #
        # No statement S in the ast can exist that threatens the control variable - which is defined as:
        #       a) control variable cannot be the left side (variable access) for an assignment statement
        #       b) control variable cannot be passed as a variable parameter (ByRef) to a procedure or function
        #       c) control variable cannot be passed into read() or readln()
        #       d) control variable is used as a control variable for a nested for statement (as interpreted by
        #          Cooper, p.27
        assert isinstance(ast, AST)

        if ast.token.token_type == TokenType.ASSIGNMENT:
            if ast.children[0].token.value.lower() == controlvariableidentifier.lower():
                error_str = "Cannot assign a value to the control variable '{}' of a 'for' statement"
                error_str = error_str.format(controlvariableidentifier)
                raise TACException(compiler_error_str(error_str, ast.children[0].token))
            self.validate_controlvariable_notthreatened(controlvariableidentifier, ast.children[1])
        elif ast.token.token_type == TokenType.IDENTIFIER:
            sym = self.symbol_table.fetch(ast.token.value)
            if isinstance(sym, ActivationSymbol):
                # procedure or function call - check to see if any of the parameters are the control variable
                for i in range(0, len(ast.children)):
                    child = ast.children[i]
                    if child.token.value.lower() == controlvariableidentifier.lower():
                        if sym.parameter_list[i].is_by_ref:
                            error_str = "Cannot pass control variable '{}' of a 'for' statement as variable parameter "
                            error_str += "'{}' to '{}'"
                            error_str = error_str.format(controlvariableidentifier, sym.parameter_list[i].symbol.name,
                                                   sym.name)
                            raise TACException(compiler_error_str(error_str, child.token))
        elif ast.token.token_type == TokenType.FOR:
            if ast.children[0].children[0].token.value.lower() == controlvariableidentifier.lower():
                error_str = "Cannot use control variable '{}' of a 'for' statement as a control variable of a nested 'for'"
                error_str = error_str.format(controlvariableidentifier)
                raise TACException(compiler_error_str(error_str, ast.children[0].children[0].token))
            else:
                self.validate_controlvariable_notthreatened(controlvariableidentifier, ast.children[0].children[1])
                self.validate_controlvariable_notthreatened(controlvariableidentifier, ast.children[1])
                self.validate_controlvariable_notthreatened(controlvariableidentifier, ast.children[2])
        else:
            for child in ast.children:
                self.validate_controlvariable_notthreatened(controlvariableidentifier, child)

        return True

    def processast_repetitivestatement(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.REPEAT, TokenType.WHILE, TokenType.FOR)

        tok = ast.token
        if tok.token_type == TokenType.FOR:
            assert len(ast.children) == 3, "TACBlock.processast - For ASTs must have 3 children"

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

            assignmentast = ast.children[0]
            assert len(assignmentast.children) == 2
            todowntoast = ast.children[1]
            assert todowntoast.token.token_type in (TokenType.TO, TokenType.DOWNTO)
            assert len(todowntoast.children) == 1
            bodyast = ast.children[2]

            # need to assign the initial and final value to temp1 and temp2 so that any changes to variables
            # in the initial and final value have no impact on the for statement.  See Cooper p.28 and p.29
            initialvalue = self.processast(assignmentast.children[1])
            temp1 = Symbol(self.get_temporary(), initialvalue.location, initialvalue.pascal_type)
            self.symbol_table.add(temp1)

            if isinstance(initialvalue, IntegerLiteral):
                self.add_node(TACUnaryLiteralNode(temp1, TACOperator.ASSIGN, initialvalue))
            else:
                self.add_node(TACUnaryNode(temp1, TACOperator.ASSIGN, initialvalue))

            finalvalue = self.processast(todowntoast.children[0])
            temp2 = Symbol(self.get_temporary(), finalvalue.location, finalvalue.pascal_type)
            self.symbol_table.add(temp2)
            if isinstance(finalvalue, IntegerLiteral):
                self.add_node(TACUnaryLiteralNode(temp2, TACOperator.ASSIGN, finalvalue))
            else:
                self.add_node(TACUnaryNode(temp2, TACOperator.ASSIGN, finalvalue))

            controlvartoken = assignmentast.children[0].token
            assert isinstance(controlvartoken, Token)

            # Enforce rule 1 from above
            if not ast.nearest_symbol_table().exists(controlvartoken.value):
                error_str = "Control variable '{}' must be declared in same block as the 'for'"
                error_str = error_str.format(controlvartoken.value)
                raise TACException(compiler_error_str(error_str, controlvartoken))

            controlvarsym = self.symbol_table.fetch(controlvartoken.value)
            controlvarsym.is_assigned_to = True
            assert isinstance(controlvarsym, Symbol)

            # Enforce rule 2 from above
            if not isinstance(controlvarsym.pascal_type, pascaltypes.OrdinalType):
                error_str = "'For' statements require control variables to be of ordinal type. "
                error_str += "Variable '{}' is of type '{}'".format(controlvartoken.value,
                                                                 controlvarsym.pascal_type.identifier)
                raise TACException(compiler_error_str(error_str, controlvartoken))

            if not ast.nearest_symbol_table().are_compatible(controlvarsym.pascal_type.identifier,
                                                             temp1.pascal_type.identifier):
                error_str = "Type {} not compatible with type {} in 'for' statement"
                error_str = error_str.format(controlvarsym.pascal_type.identifier, temp1.pascal_type.identifier)
                raise TACException(compiler_error_str(error_str, assignmentast.children[1].token))

            if not ast.nearest_symbol_table().are_compatible(controlvarsym.pascal_type.identifier,
                                                             temp2.pascal_type.identifier):
                error_str = "Type {} not compatible with type {} in 'for' statement"
                error_str = error_str.format(controlvarsym.pascal_type.identifier, temp2.pascal_type.identifier)
                raise TACException(compiler_error_str(error_str, todowntoast.children[0].token))

            # rule 3 will be a runtime check

            # Enforce rule 4 from above
            self.validate_controlvariable_notthreatened(controlvartoken.value, bodyast)

            # finish assembling the TAC
            # TODO - refactor processast_conditionalstatement and the while from below so we don't have
            # to be repetitive

            if todowntoast.token.token_type == TokenType.TO:
                sysfunc = Label("_SUCCO")
                compareop = TACOperator.LESS_EQUAL
            else:
                sysfunc = Label("_PREDO")
                compareop = TACOperator.GREATER_EQUAL

            labeldoneif = self.get_label()
            self.add_node(TACCommentNode("If condition is true, we execute the body once."))
            ifsym = Symbol(self.get_temporary(), assignmentast.children[1].token.location, pascaltypes.BooleanType())
            self.symbol_table.add(ifsym)
            self.add_node(TACBinaryNode(ifsym, compareop, temp1, temp2))
            self.add_node(TACIFZNode(ifsym, labeldoneif))
            self.add_node(TACUnaryNode(controlvarsym, TACOperator.ASSIGN, temp1))
            self.processast(bodyast)
            labelstartwhile = self.get_label()
            self.add_node(TACCommentNode("The for statement now becomes a while statement"))
            self.add_node(TACLabelNode(labelstartwhile))
            whilesym = Symbol(self.get_temporary(), todowntoast.children[0].token.location, pascaltypes.BooleanType())
            self.symbol_table.add(whilesym)
            self.add_node(TACBinaryNode(whilesym, TACOperator.NOT_EQUAL, controlvarsym, temp2))
            self.add_node(TACIFZNode(whilesym, labeldoneif))
            self.add_node(TACParamNode(controlvarsym))
            self.add_node(TACCallSystemFunctionNode(sysfunc, 1, controlvarsym))
            self.processast(bodyast)
            self.add_node(TACGotoNode(labelstartwhile))
            self.add_node(TACLabelNode(labeldoneif))
            # 6.8.3.9 - "After a for-statement is executed,
            # other than being left by a goto-statement, the control-variable shall be undefined"
            controlvarsym.is_assigned_to = False

        elif tok.token_type == TokenType.WHILE:
            assert len(ast.children) == 2, "TACBlock.processast - While ASTs must have 2 children"
            labelstart = self.get_label()
            labeldone = self.get_label()

            self.add_node(TACLabelNode(labelstart))
            condition = self.processast(ast.children[0])
            if not isinstance(condition.pascal_type, pascaltypes.BooleanType):
                raise TACException(
                    compiler_error_str("While statements must be followed by Boolean Expressions: ", tok))
            self.add_node(TACIFZNode(condition, labeldone))
            self.processast(ast.children[1])
            self.add_node(TACGotoNode(labelstart))
            self.add_node(TACLabelNode(labeldone))
        else:  # TokenType.REPEAT
            labelstart = self.get_label()
            self.add_node(TACLabelNode(labelstart))
            maxchild = len(ast.children) - 1
            for child in ast.children[:-1]:
                self.processast(child)
            condition = self.processast(ast.children[maxchild])
            self.add_node(TACIFZNode(condition, labelstart))

    def processast_inputoutput(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.INPUT, TokenType.OUTPUT)
        return self.symbol_table.fetch(ast.token.value)

    def processast_identifier(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type == TokenType.IDENTIFIER

        tok = ast.token
        # undefined identifiers are caught upstream
        assert self.symbol_table.exists_anywhere(tok.value)
        sym = self.symbol_table.fetch(tok.value)
        if isinstance(sym, FunctionResultVariableSymbol):
            # need to see if it's really the result of a function, or a recursive function call
            # if it is the result of a function, the parent will be an assign and this will be the left child
            if ast.parent.token.token_type == TokenType.ASSIGNMENT and ast.parent.children[0] == ast:
                pass
            else:
                # we know it is a function call, so get the activation symbol, which is stored in the parent
                sym = self.symbol_table.parent.fetch(tok.value)
        if isinstance(sym, ConstantSymbol):
            # optimization for integers - we can just return the literal itself instead of an assignment to
            # a local symbol.
            if isinstance(sym.pascal_type, pascaltypes.IntegerType):
                return IntegerLiteral(sym.value, tok.location)
            else:
                ret = ConstantSymbol(self.get_temporary(), tok.location, sym.pascal_type, sym.value)
                self.symbol_table.add(ret)
                if isinstance(sym.pascal_type, pascaltypes.BooleanType):
                    # the value of the symbol will always be a string
                    assert sym.value.lower() in ("true", "false")
                    if sym.value.lower() == 'true':
                        tokval = "1"
                    else:
                        tokval = "0"
                    lit = BooleanLiteral(tokval, tok.location)
                elif isinstance(sym.pascal_type, pascaltypes.StringLiteralType):
                    lit = StringLiteral(sym.value, tok.location)
                elif isinstance(sym.pascal_type, pascaltypes.CharacterType):
                    lit = CharacterLiteral(sym.value, tok.location)
                elif isinstance(sym.pascal_type, pascaltypes.RealType):
                    lit = RealLiteral(sym.value, tok.location)
                else:
                    assert isinstance(sym.pascal_type, pascaltypes.EnumeratedType)
                    lit = IntegerLiteral(str(sym.pascal_type.position(sym.value)), tok.location)

                self.add_node(TACUnaryLiteralNode(ret, TACOperator.ASSIGN, lit))
        elif isinstance(sym, pascaltypes.EnumeratedTypeValue):
            # need to return a symbol.
            # TODO - return the enumerated type value so that we can make it a literal here instead of a symbol
            # assign.  Cannot return an IntegerLiteral here because then it will not assign properly to values
            # of the enumerated type.  Likely need an EnumeratedTypeLiteral
            tmptype = self.symbol_table.fetch(sym.type_identifier)
            tmpsym = Symbol(self.get_temporary(), tok.location, tmptype)
            self.symbol_table.add(tmpsym)
            comment = "Convert literal '{}' to integer value {}".format(sym.identifier, sym.value)
            self.add_node(TACCommentNode(comment))
            self.add_node(TACUnaryLiteralNode(tmpsym, TACOperator.ASSIGN, IntegerLiteral(str(sym.value), tok.location)))
            return tmpsym
        elif not isinstance(sym, ActivationSymbol):
            # just return the identifier itself
            ret = sym
        else:
            # Invoke the procedure or function.  If it is a Procedure, we will return
            # nothing.  If a function, we will return a symbol that contains the return value of the
            # function.
            assert isinstance(sym, ActivationSymbol)  # removes PyCharm errors
            # children of the AST node are the parameters to the proc/func.  Validate count is correct
            if len(ast.children) != len(sym.parameter_list):
                error_str = "{} expected {} parameters, but {} provided"
                error_str = error_str.format(tok.value, len(sym.parameter_list.parameter_list), len(ast.children))
                raise TACException(compiler_error_str(error_str, tok))

            for i in range(0, len(ast.children)):
                child = ast.children[i]
                tmp = self.processast(child)

                if sym.parameter_list[i].is_by_ref:
                    # 6.6.3.3 of the ISO Standard states that if the formal parameter is a variable
                    # parameter, then the actual parameter must be the same type as the formal parameter
                    # and the actual parameter must be a variable access, meaning it cannot be a literal
                    # or the output of a function.
                    if not isinstance(tmp, VariableSymbol):
                        error_str = "Must pass in variable for parameter {} of {}()".format(
                            sym.parameter_list[i].symbol.name, sym.name)
                        raise TACException(compiler_error_str(error_str, child.token))

                    # For variable parameters, the actual parameter must have same type as the formal parameter
                    if not ast.nearest_symbol_table().are_same_type(tmp.pascal_type.identifier,
                                                                    sym.parameter_list[
                                                                        i].symbol.pascal_type.identifier):
                        error_str = "Type Mismatch - parameter {} of {}() must be type {}"
                        error_str = error_str.format(sym.parameter_list[i].symbol.name, sym.name,
                                               str(sym.parameter_list[i].symbol.pascal_type.identifier))
                        raise TACException(compiler_error_str(error_str, child.token))
                else:
                    # For value parameters, the actual parameter must be assignment compatible with the formal
                    # parameter
                    if isinstance(tmp, ConstantSymbol):
                        optval = tmp.value
                    else:
                        optval = None

                    if not ast.nearest_symbol_table().are_assignment_compatible(
                            sym.parameter_list[i].symbol.pascal_type.identifier, tmp.pascal_type.identifier, optval):
                        error_str = "Error D.7: Type Mismatch - {} is not assignment compatible with parameter "
                        error_str += "{} of {}()"
                        error_str = error_str.format(str(tmp.pascal_type.identifier),
                                               sym.parameter_list[i].symbol.name, sym.name)
                        raise TACException(compiler_error_str(error_str, child.token))

                if isinstance(tmp.pascal_type, pascaltypes.IntegerType) and \
                        isinstance(sym.parameter_list[i].symbol.pascal_type, pascaltypes.RealType):
                    tmp2 = self.process_sym_inttoreal(tmp)
                    self.add_node(TACParamNode(tmp2))
                else:
                    self.add_node(TACParamNode(tmp))

            if sym.result_type is not None:
                # means it is a function
                ret = Symbol(self.get_temporary(), tok.location, sym.result_type)
                self.symbol_table.add(ret)
            else:
                # procedures return nothing
                ret = None
            self.add_node(TACCallFunctionNode(sym.label, sym.name, len(ast.children), ret))

        return ret

    def processast_integerliteral(self, ast):
        # This function is static (no references to self) but because of what it does, I have it included in the
        # object instead of a standalone helper function.
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.UNSIGNED_INT, TokenType.SIGNED_INT, TokenType.MAXINT)

        tok = ast.token
        if tok.token_type in (TokenType.UNSIGNED_INT, TokenType.SIGNED_INT):
            ret = IntegerLiteral(tok.value, tok.location)
        else:
            assert tok.token_type == TokenType.MAXINT
            ret = IntegerLiteral(pascaltypes.MAXINT_AS_STRING, tok.location)
        return ret

    def processast_realliteral(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.SIGNED_REAL, TokenType.UNSIGNED_REAL)

        tok = ast.token
        lit = RealLiteral(tok.value, tok.location)
        littype = pascaltypes.RealType()

        ret = ConstantSymbol(self.get_temporary(), tok.location, littype, tok.value)
        self.symbol_table.add(ret)
        self.add_node(TACUnaryLiteralNode(ret, TACOperator.ASSIGN, lit))

        return ret

    def processast_booleanliteral(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.TRUE, TokenType.FALSE)

        tok = ast.token
        ret = ConstantSymbol(self.get_temporary(), tok.location, pascaltypes.BooleanType(), tok.value)
        self.symbol_table.add(ret)
        if tok.token_type == TokenType.TRUE:
            tokval = "1"  # 6.4.2.2 of ISO standard - Booleans are stored as 0 or 1 in memory
        else:
            tokval = "0"
        self.add_node(TACUnaryLiteralNode(ret, TACOperator.ASSIGN, BooleanLiteral(tokval, tok.location)))
        return ret

    def processast_characterstring(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type == TokenType.CHARSTRING

        tok = ast.token

        litval = tok.value
        # string of length 1 is a character.  String of any other length is a string literal
        if len(litval) != 1:
            littype = pascaltypes.StringLiteralType()
            lit = StringLiteral(litval, tok.location)
        else:
            littype = pascaltypes.CharacterType()
            lit = CharacterLiteral(litval, tok.location)

        ret = ConstantSymbol(self.get_temporary(), tok.location, littype, litval)
        self.symbol_table.add(ret)
        self.add_node(TACUnaryLiteralNode(ret, TACOperator.ASSIGN, lit))
        return ret

    def processast_array(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type == TokenType.LEFT_BRACKET
        assert len(ast.children) == 2, "TACBlock.processast_array - Array ASTs must have 2 children."

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
            a pointer to the componenttype for the array.  Return this symbol.
        '''

        step1 = self.processast(ast.children[0])
        assert isinstance(step1.pascal_type, pascaltypes.ArrayType) or \
               (isinstance(step1.pascal_type, pascaltypes.PointerType) and
                isinstance(step1.pascal_type.points_to_type, pascaltypes.ArrayType))

        if isinstance(step1.pascal_type, pascaltypes.ArrayType):
            arraytype = step1.pascal_type
            assignop = TACOperator.ASSIGN_ADDRESS_OF
        else:
            arraytype = step1.pascal_type.points_to_type
            assert isinstance(arraytype, pascaltypes.ArrayType)
            assignop = TACOperator.ASSIGN

        componenttype = arraytype.component_type
        indextype = arraytype.index_type

        step2 = Symbol(self.get_temporary(), step1.location, componenttype.get_pointer_to())
        self.symbol_table.add(step2)
        self.add_node(TACUnaryNode(step2, assignop, step1))

        step3 = self.dereference_if_needed(self.processast(ast.children[1]), ast.children[1].token)

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
            minrange = indextype.range_min_int
            maxrange = indextype.range_max_int
        else:
            assert isinstance(indextype, pascaltypes.OrdinalType)
            if isinstance(indextype, pascaltypes.IntegerType):
                error_str = compiler_error_str("Cannot have an array with index range 'integer'", ast.token)
                raise TACException(error_str)
            minrange = indextype.position(indextype.min_item())
            maxrange = indextype.position(indextype.max_item())

        if isinstance(step3, IntegerLiteral):
            # we can do the math in the compiler
            if int(step3.value) < minrange or int(step3.value) > maxrange:
                error_str = compiler_error_str("Array Index '{}' out of range".format(step3.value), ast.children[1].token)
                raise TACException(error_str)

            indexpos = (int(step3.value) - minrange)
            numbytes = indexpos * componenttype.size
            step4 = IntegerLiteral(str(numbytes), step1.location)
        else:
            step4a = Symbol(self.get_temporary(), step1.location, pascaltypes.IntegerType())
            indexmin_literal = IntegerLiteral(str(minrange), step1.location)
            size_literal = IntegerLiteral(str(componenttype.size), step1.location)
            self.symbol_table.add(step4a)
            self.add_node(TACBinaryNode(step4a, TACOperator.SUBTRACT, step3, indexmin_literal))
            step4 = Symbol(self.get_temporary(), step1.location, pascaltypes.IntegerType())
            self.symbol_table.add(step4)
            self.add_node(TACBinaryNode(step4, TACOperator.MULTIPLY, step4a, size_literal))

        step5 = Symbol(self.get_temporary(), step1.location, step2.pascal_type)
        self.symbol_table.add(step5)

        self.add_node(TACBinaryNodeWithBoundsCheck(step5, TACOperator.ADD, step2, step4, 0, arraytype.size - 1))
        return step5

    def processast_assignment(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type == TokenType.ASSIGNMENT
        assert len(ast.children) == 2, "TACBlock.processast_assignment - Assignment ASTs must have 2 children."

        lval = self.processast(ast.children[0])
        if isinstance(lval.pascal_type, pascaltypes.PointerType):
            lval_reftype = lval.pascal_type.points_to_type
            assignop = TACOperator.ASSIGN_TO_DEREFERENCE
        else:
            lval_reftype = lval.pascal_type
            assignop = TACOperator.ASSIGN

        # assigning to constant is caught upstream
        assert not isinstance(lval, ConstantSymbol), "TAC Error: attempted to assign to constant"

        rval = self.dereference_if_needed(self.processast(ast.children[1]), ast.children[1].token)

        if isinstance(rval, pascaltypes.EnumeratedTypeValue):
            # Note 2025-11-09 - unsure how to execute this block, may need to assert that we do not have
            # an enumerated type as an rval
            comment = "Convert literal {} to integer value {}".format(rval.identifier, rval.value)
            self.add_node(TACCommentNode(comment))
            self.add_node(TACUnaryLiteralNode(lval, TACOperator.ASSIGN,
                                              IntegerLiteral(str(rval.value), ast.children[1].token.location)))
        else:
            if isinstance(rval, ConstantSymbol) or isinstance(rval, IntegerLiteral):
                t2value = rval.value
            else:
                t2value = None

            if not ast.nearest_symbol_table().are_assignment_compatible(lval_reftype.identifier,
                                                                        rval.pascal_type.identifier, t2value):
                if t2value is not None:
                    error_str = "Cannot assign value '{}' of type {} to type {}"
                    if isinstance(rval.pascal_type, pascaltypes.OrdinalType):
                        # the error in 6.8.2.2 is specific to ordinal types.
                        error_str = "Error D.49: " + error_str
                    error_str = error_str.format(t2value, rval.pascal_type.identifier, lval_reftype.identifier)
                else:
                    error_str = "Cannot assign {} type to {}".format(rval.pascal_type.identifier, lval_reftype.identifier)
                raise TACException(compiler_error_str(error_str, ast.children[1].token))
            if isinstance(lval_reftype, pascaltypes.RealType) and \
                    isinstance(rval.pascal_type, pascaltypes.IntegerType):
                newrval = self.process_sym_inttoreal(rval)
            else:
                newrval = rval

            lval.is_assigned_to = True

            if isinstance(newrval, Literal):
                self.add_node(TACUnaryLiteralNode(lval, assignop, newrval))
            else:
                self.add_node(TACUnaryNode(lval, assignop, newrval))
        return lval

    def process_sym_inttoreal(self, sym):
        # sym is a symbol of integer type.  Returns a symbol that converts token to a real type
        assert isinstance(sym, Symbol) or isinstance(sym, IntegerLiteral)
        if isinstance(sym, Symbol):
            assert isinstance(sym.pascal_type, pascaltypes.IntegerType)
        ret = Symbol(self.get_temporary(), sym.location, pascaltypes.RealType())
        self.symbol_table.add(ret)
        if isinstance(sym, Symbol):
            self.add_node(TACUnaryNode(ret, TACOperator.INT_TO_REAL, sym))
        else:
            self.add_node(TACUnaryLiteralNode(ret, TACOperator.INT_TO_REAL, sym))
        return ret

    def processast_arithmeticoperator(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.MULTIPLY, TokenType.PLUS, TokenType.MINUS, TokenType.DIVIDE,
                                        TokenType.INTEGER_DIV, TokenType.MOD)
        assert len(ast.children) == 2

        tok = ast.token
        op = map_token_type_to_tac_operator(tok.token_type)
        child1 = self.dereference_if_needed(self.processast(ast.children[0]), ast.children[0].token)
        child2 = self.dereference_if_needed(self.processast(ast.children[1]), ast.children[1].token)

        if isinstance(child1.pascal_type, pascaltypes.BooleanType) or \
                isinstance(child2.pascal_type, pascaltypes.BooleanType):
            raise TACException(compiler_error_str("Cannot use boolean type with math operators", tok))

        if tok.token_type in (TokenType.INTEGER_DIV, TokenType.MOD) and \
                (isinstance(child1.pascal_type, pascaltypes.RealType) or
                 isinstance(child2.pascal_type, pascaltypes.RealType)):
            raise TACException(compiler_error_str("Cannot use integer division with real values.", tok))

        # The addition, subtraction, multiplication operators can take integers or reals, and return
        # integer if both operands are integers, or a real if one or both operands are reals.  The
        # division operator returns a real even if both operands are integers
        if isinstance(child1.pascal_type, pascaltypes.RealType) or \
                isinstance(child2.pascal_type, pascaltypes.RealType) or \
                op == TACOperator.DIVIDE:

            # 6.7.2.1 of the ISO Standard states that if either operand of addition, subtraction, or multiplication
            # are real-type, then the result will also be real-type.  Similarly, if the "/" operator is used,
            # even if both operands are integer-type, the result is real-type.  Cooper states on p.31 that
            # "[t]his means that integer operands are sometimes coerced into being reals; i.e. they are temporarily
            # treated as values of type real."
            if isinstance(child1.pascal_type, pascaltypes.IntegerType):
                newchild1 = self.process_sym_inttoreal(child1)
            else:
                newchild1 = child1

            if isinstance(child2.pascal_type, pascaltypes.IntegerType):
                newchild2 = self.process_sym_inttoreal(child2)
            else:
                newchild2 = child2

            ret = Symbol(self.get_temporary(), tok.location, pascaltypes.RealType())
            self.symbol_table.add(ret)
            self.add_node(TACBinaryNode(ret, op, newchild1, newchild2))
        else:
            ret = Symbol(self.get_temporary(), tok.location, pascaltypes.IntegerType())
            self.symbol_table.add(ret)
            self.add_node(TACBinaryNode(ret, op, child1, child2))

        return ret

    def processast_relationaloperator(self, ast):
        assert isinstance(ast, AST)
        assert is_relational_operator(ast.token.token_type)

        tok = ast.token
        op = map_token_type_to_tac_operator(tok.token_type)
        child1 = self.dereference_if_needed(self.processast(ast.children[0]), ast.children[0].token)
        child2 = self.dereference_if_needed(self.processast(ast.children[1]), ast.children[1].token)

        c1type = child1.pascal_type
        c2type = child2.pascal_type

        # 6.7.2.5 of the ISO standard says that the operands of relational operators shall be of compatible
        # types, or one operand shall be of real-type and the other of integer-type.  Table 6, has
        # simple-types, pointer-types, and string-types allowed in the comparisons.

        # special case for string literals - symbol_table.are_compatible() just looks at the identifiers,
        # which works fine for every time other than string literals doing relational comparisons.  For
        # string literals we need to look at the length to know if they are compatible.

        if not self.symbol_table.are_compatible(c1type.identifier, c2type.identifier, child1, child2):
            if isinstance(c1type, pascaltypes.IntegerType) and isinstance(c2type, pascaltypes.RealType):
                pass
            elif isinstance(c2type, pascaltypes.IntegerType) and isinstance(c1type, pascaltypes.RealType):
                pass
            elif isinstance(c1type, pascaltypes.BooleanType) or isinstance(c2type, pascaltypes.BooleanType):
                raise TACException(compiler_error_str("Cannot compare Boolean to non-Boolean", tok))
            else:
                error_str = "Cannot compare types '{}' and '{}' with relational operator"
                error_str = error_str.format(c1type.identifier, c2type.identifier)
                raise TACException(compiler_error_str(error_str, tok))

        if isinstance(c1type, pascaltypes.IntegerType) and isinstance(c2type, pascaltypes.RealType):
            newchild1 = self.process_sym_inttoreal(child1)
        else:
            newchild1 = child1
        if isinstance(c2type, pascaltypes.IntegerType) and isinstance(c1type, pascaltypes.RealType):
            newchild2 = self.process_sym_inttoreal(child2)
        else:
            newchild2 = child2

        ret = Symbol(self.get_temporary(), tok.location, pascaltypes.BooleanType())
        self.symbol_table.add(ret)
        self.add_node(TACBinaryNode(ret, op, newchild1, newchild2))
        return ret

    def processast_booleanoperator(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.AND, TokenType.OR, TokenType.NOT)

        tok = ast.token
        op = map_token_type_to_tac_operator(tok.token_type)

        if tok.token_type in (TokenType.AND, TokenType.OR):
            child1 = self.dereference_if_needed(self.processast(ast.children[0]), ast.children[0].token)
            child2 = self.dereference_if_needed(self.processast(ast.children[1]), ast.children[1].token)
            if not isinstance(child1.pascal_type, pascaltypes.BooleanType) or \
                    not isinstance(child2.pascal_type, pascaltypes.BooleanType):
                error_str = "Both arguments to operator '{}' must be Boolean type".format(tok.value)
                raise TACException(compiler_error_str(error_str, tok))
            ret = Symbol(self.get_temporary(), tok.location, pascaltypes.BooleanType())
            self.symbol_table.add(ret)
            self.add_node(TACBinaryNode(ret, op, child1, child2))
        else:  # token.token_type == TokenType.NOT
            child = self.dereference_if_needed(self.processast(ast.children[0]), ast.children[0].token)
            if not isinstance(child.pascal_type, pascaltypes.BooleanType):
                raise TACException(compiler_error_str("Operator 'not' can only be applied to Boolean factors", tok))
            ret = Symbol(self.get_temporary(), tok.location, pascaltypes.BooleanType())
            self.symbol_table.add(ret)
            self.add_node(TACUnaryNode(ret, op, child))
        return ret

    def processast(self, ast):
        """ returns the Symbol of a temporary that holds the result of this computation, or None """

        assert isinstance(ast, AST)
        if ast.comment != "":
            self.add_node(TACCommentNode(ast.comment))

        tok = ast.token
        toktype = ast.token.token_type

        # Begin statements, Procedure/Function declarations, Output, Conditionals, and Repetitive statements
        # do not return anything.  Identifiers generally do, unless they are procedure calls.  Everything else
        # returns a symbol.

        ret = None

        if toktype == TokenType.BEGIN:
            self.process_ast_begin(ast)
        elif toktype in (TokenType.PROCEDURE, TokenType.FUNCTION):
            self.process_ast_procedure_or_function(ast)
        elif toktype in (TokenType.RESET, TokenType.REWRITE):
            self.processast_fileprocedure(ast)
        elif toktype in (TokenType.WRITE, TokenType.WRITELN):
            self.processast_write(ast)
        elif toktype == TokenType.GOTO:
            self.process_ast_goto(ast)
        elif toktype == TokenType.IF:
            self.processast_conditionalstatement(ast)
        elif toktype in (TokenType.WHILE, TokenType.REPEAT, TokenType.FOR):
            self.processast_repetitivestatement(ast)
        elif is_iso_required_function(tok.token_type):
            ret = self.processast_isorequiredfunction(ast)
        elif toktype == TokenType.LEFT_BRACKET:
            ret = self.processast_array(ast)
        elif toktype == TokenType.ASSIGNMENT:
            ret = self.processast_assignment(ast)
        elif toktype == TokenType.IDENTIFIER:
            ret = self.processast_identifier(ast)
        elif tok.token_type in (TokenType.INPUT, TokenType.OUTPUT):
            ret = self.processast_inputoutput(ast)
        elif tok.token_type in (TokenType.UNSIGNED_INT, TokenType.SIGNED_INT, TokenType.MAXINT):
            ret = self.processast_integerliteral(ast)
        elif tok.token_type in (TokenType.UNSIGNED_REAL, TokenType.SIGNED_REAL):
            ret = self.processast_realliteral(ast)
        elif tok.token_type in [TokenType.TRUE, TokenType.FALSE]:
            ret = self.processast_booleanliteral(ast)
        elif tok.token_type == TokenType.CHARSTRING:
            ret = self.processast_characterstring(ast)
        elif tok.token_type in (TokenType.MULTIPLY, TokenType.PLUS, TokenType.MINUS, TokenType.DIVIDE,
                                TokenType.INTEGER_DIV, TokenType.MOD):
            ret = self.processast_arithmeticoperator(ast)
        elif is_relational_operator(tok.token_type):
            ret = self.processast_relationaloperator(ast)
        elif tok.token_type in (TokenType.AND, TokenType.OR, TokenType.NOT):
            ret = self.processast_booleanoperator(ast)
        elif tok.token_type == TokenType.EMPTY_TOKEN:
            self.add_node(TACNoOpNode())
        else:  # pragma: no cover
            raise TACException(compiler_error_str("TACBlock.processast - cannot process token:".format(str(tok)), tok))

        assert ret is None or isinstance(ret, Symbol) or isinstance(ret, IntegerLiteral)
        return ret


class TACGenerator:
    def __init__(self, literaltable):
        assert isinstance(literaltable, LiteralTable)
        self.tacblocks = []
        self.nextlabel = 0
        self.nexttemporary = 0
        self.globalsymboltable = SymbolTable()
        self.globalliteraltable = deepcopy(literaltable)
        self.warningslist = []

    def addblock(self, block):
        assert isinstance(block, TACBlock)
        self.tacblocks.append(block)

    def generateblock(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type in (TokenType.BEGIN, TokenType.PROCEDURE, TokenType.FUNCTION)
        # process the main begin
        if ast.token.token_type == TokenType.BEGIN:
            newblock = TACBlock(True, self)
        else:
            newblock = TACBlock(False, self)
            newblock.symbol_table = deepcopy(ast.symbol_table)
        newblock.symbol_table.parent = self.globalsymboltable
        newblock.processast(ast)
        return newblock

    def generate(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.token_type == TokenType.PROGRAM
        self.globalsymboltable = deepcopy(ast.symbol_table)

        for child in ast.children:
            self.addblock(self.generateblock(child))
        # insure there is exactly one main block
        mainblockcount = 0
        for block in self.tacblocks:
            if block.is_main:
                mainblockcount += 1
        assert (mainblockcount == 1), \
            "TACGenerator.generate created {} main blocks instead of 1".format(str(mainblockcount))

    def getlabel(self, labelsuffix=""):
        # labels begin with _TAC_L so that they do not collide with the labels generated in asmgenerator.
        label = Label("_TAC_L{}_{}".format(str(self.nextlabel), labelsuffix))
        self.nextlabel += 1
        return label

    def gettemporary(self):
        temporary = "_T" + str(self.nexttemporary)
        self.nexttemporary += 1
        return temporary

    def printblocks(self):  # pragma: no cover
        for block in self.tacblocks:
            if block.is_main:
                print("_MAIN:")
            block.print_nodes()
