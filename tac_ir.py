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
from parser import AST, isrelationaloperator, is_isorequiredfunction
from symboltable import Symbol, Label, Literal, IntegerLiteral, RealLiteral, StringLiteral, BooleanLiteral,\
    SymbolTable, LiteralTable, ParameterList, ActivationSymbol, Parameter, VariableSymbol,\
    FunctionResultVariableSymbol, ConstantSymbol, CharacterLiteral
from lexer import TokenType, Token
import pascaltypes


class TACException(Exception):
    pass


def tac_errstr(msg, tok=None):
    errstr = msg
    if tok is not None:
        assert(isinstance(tok, Token))
        errstr += " in {0}".format(str(tok.location))
    return errstr


@unique
class TACOperator(Enum):
    LABEL = "label"
    ASSIGN = ":="
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    IDIV = "div"
    MOD = "mod"
    EQUALS = "="
    NOTEQUAL = "<>"
    LESS = "<"
    LESSEQ = "<="
    GREATER = ">"
    GREATEREQ = ">="
    ASSIGNADDRESSOF = ":= &"
    ASSIGNTODEREF = "* :="
    ASSIGNDEREFTO = ":= *"
    AND = "and"
    OR = "or"
    NOT = "not"
    PARAM = "param"
    CALL = "call"
    COMMENT = "comment"
    INTTOREAL = "is int_to_real"
    IFZ = "ifz"
    GOTO = "goto"
    RETURN = "return"

    def __str__(self):
        return self.value


def maptokentype_to_tacoperator(tokentype):
    # Token Types have equivalent TACOperators, this is a mapping
    assert isinstance(tokentype, TokenType)
    assert tokentype in (TokenType.EQUALS, TokenType.NOTEQUAL, TokenType.LESS, TokenType.LESSEQ, TokenType.GREATER,
                         TokenType.GREATEREQ, TokenType.IDIV, TokenType.MOD, TokenType.MULTIPLY, TokenType.PLUS,
                         TokenType.MINUS, TokenType.DIVIDE, TokenType.AND, TokenType.OR, TokenType.NOT)
    if tokentype == TokenType.EQUALS:
        ret = TACOperator.EQUALS
    elif tokentype == TokenType.NOTEQUAL:
        ret = TACOperator.NOTEQUAL
    elif tokentype == TokenType.LESS:
        ret = TACOperator.LESS
    elif tokentype == TokenType.LESSEQ:
        ret = TACOperator.LESSEQ
    elif tokentype == TokenType.GREATER:
        ret = TACOperator.GREATER
    elif tokentype == TokenType.GREATEREQ:
        ret = TACOperator.GREATEREQ
    elif tokentype == TokenType.NOT:
        ret = TACOperator.NOT
    elif tokentype == TokenType.AND:
        ret = TACOperator.AND
    elif tokentype == TokenType.OR:
        ret = TACOperator.OR
    elif tokentype == TokenType.IDIV:
        ret = TACOperator.IDIV
    elif tokentype == TokenType.MOD:
        ret = TACOperator.MOD
    elif tokentype == TokenType.MULTIPLY:
        ret = TACOperator.MULTIPLY
    elif tokentype == TokenType.PLUS:
        ret = TACOperator.ADD
    elif tokentype == TokenType.MINUS:
        ret = TACOperator.SUBTRACT
    else:
        assert tokentype == TokenType.DIVIDE
        ret = TACOperator.DIVIDE
    return ret


def invalidparm_forsystemfunction_errstr(tok, str_requiredtypes):
    assert isinstance(tok, Token)
    return "Function {}() requires {} parameter in {}".format(tok.tokentype, str_requiredtypes, tok.location)


def requiredfunction_acceptsreal(tokentype):
    # The arithmetic functions in 6.6.6.2 all accept reals as do the transfer functions in 6.6.6.3.
    assert isinstance(tokentype, TokenType)
    if tokentype in (TokenType.ABS, TokenType.SQR, TokenType.SIN, TokenType.COS, TokenType.EXP,
                     TokenType.LN, TokenType.SQRT, TokenType.ARCTAN, TokenType.TRUNC, TokenType.ROUND):
        return True
    else:
        return False


def requiredfunction_acceptsinteger(tokentype):
    # abs() and sqr() in 6.6.6.2, chr() in 6.6.6.4, and odd() from 6.6.6.5 accept integers
    assert isinstance(tokentype, TokenType)
    if tokentype in (TokenType.ABS, TokenType.SQR, TokenType.CHR, TokenType.ODD):
        return True
    else:
        return False


def requiredfunction_acceptsinteger_or_real(tokentype):
    # abs() and sqr() in 6.6.6.2 accept both integer or real
    assert isinstance(tokentype, TokenType)
    if tokentype in (TokenType.ABS, TokenType.SQR):
        return True
    else:
        return False


def requiredfunction_acceptsordinal(tokentype):
    # ord(), succ(), pred() in 6.6.6.4 accept ordinals
    assert isinstance(tokentype, TokenType)
    if tokentype in (TokenType.ORD, TokenType.SUCC, TokenType.PRED):
        return True
    else:
        return False


def requiredfunction_returntype(tokentype, paramtypedef):
    # abs() and sqr() in 6.6.6.2 as well as succ() and pred() in 6.6.6.4 return same type as parameter
    # Remaining functions in 6.6.6.2 return reals
    # Transfer functions in 6.6.6.3 return ints
    # ord() in 6.6.6.4 returns int.
    # chr() in 6.6.6.4 returns char
    # functions in 6.6.6.5 return Boolean
    if tokentype in (TokenType.ABS, TokenType.SQR, TokenType.SUCC, TokenType.PRED):
        # this is a bit of hackery but it works
        ret = deepcopy(paramtypedef)
    elif tokentype in (TokenType.SIN, TokenType.COS, TokenType.EXP, TokenType.LN, TokenType.SQRT, TokenType.ARCTAN):
        ret = pascaltypes.SIMPLETYPEDEF_REAL
    elif tokentype in (TokenType.TRUNC, TokenType.ROUND, TokenType.ORD):
        ret = pascaltypes.SIMPLETYPEDEF_INTEGER
    elif tokentype == TokenType.CHR:
        ret = pascaltypes.SIMPLETYPEDEF_CHAR
    else:
        assert tokentype in (TokenType.ODD, TokenType.EOF, TokenType.EOLN)
        ret = pascaltypes.SIMPLETYPEDEF_BOOLEAN
    return ret


def maptoken_to_systemfunction_name(tok, typechar):
    assert isinstance(tok, Token)
    return "_{}{}".format(str(tok.tokentype).upper(), typechar.upper())


class TACNode:
    def __init__(self, operator):
        assert isinstance(operator, TACOperator)
        self.operator = operator


class TACCommentNode(TACNode):
    def __init__(self, comment):
        assert isinstance(comment, str)
        super().__init__(TACOperator.COMMENT)
        self.comment = comment

    def __str__(self):
        return "\t\t;{}".format(self.comment)


class TACLabelNode(TACNode):
    def __init__(self, label, comment=None):
        assert isinstance(label, Label)
        assert comment is None or isinstance(comment, str)
        super().__init__(TACOperator.LABEL)
        self.label = label
        self.comment = comment

    def __str__(self):
        return "{}:".format(self.label)


class TACDeclareFunctionNode(TACLabelNode):
    def __init__(self, label, paramlist, returntypedef=None):
        super().__init__(label)
        assert isinstance(paramlist, ParameterList)
        self.paramlist = paramlist
        assert returntypedef is None or (isinstance(returntypedef, pascaltypes.TypeDef) and
                                         isinstance(returntypedef.basetype, pascaltypes.OrdinalType))
        self.returntypedef = returntypedef

    def __str__(self):
        return ""


class TACFunctionReturnNode(TACNode):
    def __init__(self, returnval):
        assert returnval is None or isinstance(returnval, Symbol)
        super().__init__(TACOperator.RETURN)
        self.returnval = returnval

    def __str__(self):
        retstr = "return"
        if self.returnval is not None:
            retstr += " " + str(self.returnval)
        return retstr


class TACParamNode(TACNode):
    def __init__(self, paramval):
        assert isinstance(paramval, Symbol) or isinstance(paramval, IntegerLiteral)
        super().__init__(TACOperator.PARAM)
        self.paramval = paramval

    def __str__(self):
        return "{} {}".format(str(self.operator), str(self.paramval))


class TACCallFunctionNode(TACNode):
    def __init__(self, label, funcname, numparams, lval=None):
        assert isinstance(label, Label)
        assert isinstance(numparams, int)
        assert isinstance(funcname, str)
        assert lval is None or isinstance(lval, Symbol)
        assert numparams >= 0
        super().__init__(TACOperator.CALL)
        self.label = label
        self.funcname = funcname
        self.numparams = numparams
        self.lval = lval

    def __str__(self):
        if self.lval is None:
            return "{} {} [{}] {}".format(str(self.operator), self.label, self.funcname, str(self.numparams))
        else:
            return "{} := {} {} [{}]".format(str(self.lval), str(self.operator),
                                             self.label, self.funcname, str(self.numparams))


class TACCallSystemFunctionNode(TACCallFunctionNode):
    def __init__(self, label, numparams, lval=None):
        assert isinstance(label, Label)
        super().__init__(label, label.name, numparams, lval)


class TACUnaryNode(TACNode):
    def __init__(self, lval, operator, arg1):
        assert isinstance(arg1, Symbol)
        assert isinstance(lval, Symbol)
        super().__init__(operator)
        self.lval = lval
        self.arg1 = arg1

    def __str__(self):
        return "{} {} {}".format(str(self.lval), str(self.operator), str(self.arg1))


class TACUnaryLiteralNode(TACNode):
    def __init__(self, lval, operator, literal1):
        assert isinstance(lval, Symbol)
        assert isinstance(literal1, Literal)
        super().__init__(operator)
        self.lval = lval
        self.literal1 = literal1

    def __str__(self):
        if isinstance(self.literal1, StringLiteral) or isinstance(self.literal1, CharacterLiteral):
            litval = '"{}"'.format(str(self.literal1).replace('"', '\"'))
        else:
            litval = str(self.literal1)
        return "{} {} {}".format(str(self.lval), str(self.operator), litval)


class TACBinaryNode(TACNode):
    def __init__(self, result, operator, arg1, arg2):
        assert isinstance(result, Symbol)
        assert isinstance(arg1, Symbol) or isinstance(arg1, IntegerLiteral)
        assert isinstance(arg2, Symbol) or isinstance(arg2, IntegerLiteral)
        super().__init__(operator)
        self.result = result
        self.arg1 = arg1
        self.arg2 = arg2

    def __str__(self):
        return "{} := {} {} {}".format(str(self.result), str(self.arg1), str(self.operator), str(self.arg2))


class TACBinaryNodeWithBoundsCheck(TACBinaryNode):
    def __init__(self, result, operator, arg1, arg2, lowerbound, upperbound):
        # Note - this is possibly a hack, because it's 5 arguments, but the alternative is to do a much longer
        # string where I get the result, then write the explicit test for less than the min and greater than the
        # max and throw the runtime error from within the TAC.  It would be the first runtime error enforced in the
        # TAC, so I don't want to extend the TAC to do that right now.
        assert isinstance(arg1, Symbol)
        assert isinstance(arg1.typedef, pascaltypes.PointerTypeDef)
        assert isinstance(lowerbound, int)
        assert isinstance(upperbound, int)
        super().__init__(result, operator, arg1, arg2)
        self.lowerbound = lowerbound
        self.upperbound = upperbound

    def __str__(self):
        ret = super().__str__()
        ret += " ; {} must have lowerbound {} and upperbound {}"
        ret = ret.format(self.arg2.name, self.lowerbound, self.upperbound)
        return ret


class TACGotoNode(TACNode):
    def __init__(self, label):
        assert isinstance(label, Label)
        super().__init__(TACOperator.GOTO)
        self.label = label

    def __str__(self):
        return "{} {}".format(str(self.operator), str(self.label))


class TACIFZNode(TACNode):
    def __init__(self, val, label):
        assert isinstance(val, Symbol)
        assert isinstance(label, Label)
        super().__init__(TACOperator.IFZ)
        self.val = val
        self.label = label

    def __str__(self):
        return "{} {} GOTO {}".format(str(self.operator), str(self.val), str(self.label))


class TACBlock:
    """ For now, assume a TACBlock represents a Pascal Block.  Not entirely language-independent but
    will work.

    NOTE: For it really to be a Pascal block, we will need to have TACBlocks within TACBlocks when
    we allow procedures and functions to be declared within another procedure or function.  This
    could in theory be done with a TACNode that contains a TACBlock?  Need to figure that out later.

    Purpose of having the generator as a member variable is so that the getlabel() / gettemporary()
    can leverage the counters in the generator.
    """
    def __init__(self, ismain, generator):
        assert isinstance(ismain, bool)
        assert isinstance(generator, TACGenerator)
        self.ismain = ismain
        self.tacnodes = []
        self.symboltable = SymbolTable()
        self.paramlist = None
        self.generator = generator

    def getlabel(self, labelsuffix=""):
        return self.generator.getlabel(labelsuffix)

    def gettemporary(self):
        return self.generator.gettemporary()

    def gettypetemporary(self):
        return self.generator.gettypetemporary()

    def addnode(self, node):
        assert isinstance(node, TACNode)
        self.tacnodes.append(node)

    def printnodes(self):
        for node in self.tacnodes:
            print(str(node))

    def processast_begin(self, ast):
        assert isinstance(ast, AST)
        for child in ast.children:
            self.processast(child)

    def deref_ifneeded(self, sym):
        assert isinstance(sym, Symbol) or isinstance(sym, Literal)
        if isinstance(sym, Literal):
            return sym
        elif isinstance(sym.typedef, pascaltypes.PointerTypeDef):
            # TODO - this works fine now when the only pointers we use are arrays.  But once we have actual pointers,
            # we won't necessarily want to deref them.  So we will need a way to test whether the sym is a real pointer
            # or a pointer to an array value.  Maybe a subclass off of pascaltypes.PointerTypeDef?

            # make a new symbol that has as its base type, the base type of the pointer
            # assign deref of the pointer to the new symbol.
            basetypesym = Symbol(self.gettemporary(), sym.location, sym.typedef.pointsto_typedef)
            self.symboltable.add(basetypesym)
            self.addnode(TACUnaryNode(basetypesym, TACOperator.ASSIGNDEREFTO, sym))
            return basetypesym
        else:
            return sym

    def validate_function_returnsvalue(self, functionidentifier, ast):
        # 6.7.3 of the ISO standard states that it shall be an error if the result of a function is undefined
        # upon completion of the algorithm.  We will need a runtime check later, similar to how we need a
        # runtime check that a variable is assigned before it is used, but for now we will just validate
        # at compile time that there is at least one assignment statement with the function-identifier is
        # on the left side.
        # Per Cooper, p.77: "Every function must contain at least one assignment to its identifier."  Also,
        # "[T]he function-identifier alone ... represents a storage location ... that may only be assigned to."
        # I infer from this that you cannot set the return value of a function by passing the function-identifier
        # to a procedure as a byref argument or such.
        # TODO - Add the runtime checks described above.
        assert isinstance(ast, AST)

        if ast.token.tokentype == TokenType.ASSIGNMENT:
            if ast.children[0].token.value.lower() == functionidentifier.lower():
                return True
            else:
                return self.validate_function_returnsvalue(functionidentifier, ast.children[1])
        else:
            for child in ast.children:
                tmp = self.validate_function_returnsvalue(functionidentifier, child)
                if tmp:
                    return True
            return False

    def processast_procedurefunction(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.tokentype in (TokenType.PROCEDURE, TokenType.FUNCTION)

        # TODO - when we want to have procedures declared within procedures, this next line will fail.
        # For now, we're ensuring the Procedure/Function is the first TACNode in the list.  This
        # matters because we are going to copy the parameter list from the AST to the TACBlock
        # and cannot do that if we have multiple parameter lists for nested procs.
        # We need some other structure.
        assert len(self.tacnodes) == 0

        # first child of a Procedure or Function is an identifier with the name of the proc/func
        assert len(ast.children) >= 1
        assert ast.children[0].token.tokentype == TokenType.IDENTIFIER

        tok = ast.token
        str_procname = ast.children[0].token.value
        self.paramlist = ast.paramlist
        # need to copy each parameter into the SymbolTable.  If the parameter is a variable parameter (ByRef),
        # the type of the symbol is a pointer to the type of the Parameter.  If the parameter is a value
        # parameter (ByVal) then the type of symbol is same as type of Parameter.
        # Remember also - Paramter Lists are ordered, but Symbol Tables are not.
        for param in self.paramlist.paramlist:
            assert isinstance(param, Parameter)
            self.symboltable.add(param.symbol)

        # we need to go to the parent to fetch the activation symbol.  If we do the fetch on
        # the current node, and this is a function, we will instead get the symbol that would hold the result.
        actsym = self.symboltable.parent.fetch(str_procname)
        assert isinstance(actsym, ActivationSymbol)
        proclabel = self.getlabel(str_procname)
        actsym.label = proclabel
        if tok.tokentype == TokenType.FUNCTION:
            comment = "Function {}({})".format(str_procname, str(self.paramlist))
        else:
            comment = "Procedure {}({})".format(str_procname, str(self.paramlist))
        self.addnode(TACLabelNode(proclabel, comment))

        for child in ast.children[1:]:
            self.processast(child)

        if tok.tokentype == TokenType.FUNCTION:
            function_has_returnvalue = self.validate_function_returnsvalue(str_procname, ast)
            if not function_has_returnvalue:
                errstr = 'Error D.48: Function {} must have a return value'.format(str_procname)
                raise TACException(tac_errstr(errstr, tok))
            self.addnode(TACFunctionReturnNode(self.symboltable.fetch(str_procname)))
        else:
            self.addnode(TACFunctionReturnNode(None))

    def processast_isorequiredfunction(self, ast):
        assert isinstance(ast, AST)
        assert is_isorequiredfunction(ast.token.tokentype)

        tok = ast.token
        tmp = self.deref_ifneeded(self.processast(ast.children[0]))
        lval = Symbol(self.gettemporary(), tok.location,
                      requiredfunction_returntype(tok.tokentype, tmp.typedef))
        self.symboltable.add(lval)
        if requiredfunction_acceptsordinal(tok.tokentype):
            if isinstance(tmp.typedef.basetype, pascaltypes.OrdinalType):
                self.addnode(TACParamNode(tmp))
                self.addnode(TACCallSystemFunctionNode(Label(maptoken_to_systemfunction_name(tok, "O")), 1, lval))
            else:
                errstr = "Function {}() requires parameter of ordinal type in {}".format(tok.tokentype,
                                                                                         tok.location)
                raise TACException(errstr)

        elif requiredfunction_acceptsinteger_or_real(tok.tokentype):
            if isinstance(tmp.typedef.basetype, pascaltypes.IntegerType):
                self.addnode(TACParamNode(tmp))
                self.addnode(TACCallSystemFunctionNode(Label(maptoken_to_systemfunction_name(tok, "I")), 1, lval))
            elif isinstance(tmp.typedef.basetype, pascaltypes.RealType):
                self.addnode(TACParamNode(tmp))
                self.addnode(TACCallSystemFunctionNode(Label(maptoken_to_systemfunction_name(tok, "R")), 1, lval))
            else:
                errstr = "Function {}() requires parameter of integer or real type in {}".format(tok.tokentype,
                                                                                                 tok.location)
                raise TACException(errstr)
        elif requiredfunction_acceptsinteger(tok.tokentype):
            if isinstance(tmp.typedef.basetype, pascaltypes.IntegerType):
                self.addnode(TACParamNode(tmp))
                self.addnode(TACCallSystemFunctionNode(Label(maptoken_to_systemfunction_name(tok, "I")), 1, lval))
            else:
                errstr = "Function {}() requires parameter of integer type in {}".format(tok.tokentype,
                                                                                         tok.location)
                raise TACException(errstr)
        else:
            assert requiredfunction_acceptsreal(tok.tokentype)
            if isinstance(tmp.typedef.basetype, pascaltypes.IntegerType):
                tmp2 = self.process_sym_inttoreal(tmp)
                self.addnode(TACParamNode(tmp2))
                self.addnode(TACCallSystemFunctionNode(Label(maptoken_to_systemfunction_name(tok, "R")), 1, lval))
            elif isinstance(tmp.typedef.basetype, pascaltypes.RealType):
                self.addnode(TACParamNode(tmp))
                self.addnode(TACCallSystemFunctionNode(Label(maptoken_to_systemfunction_name(tok, "R")), 1, lval))
            else:
                # sqr() and abs() accept integer and real, others only accept reals
                if tok.tokentype in (TokenType.SQR, TokenType.ABS):
                    errstr = "Function {}() requires parameter of integer or real type in {}"
                else:
                    errstr = "Function {}() requires parameter of real type in {}"
                errstr = errstr.format(tok.tokentype, tok.location)
                raise TACException(errstr)
        return lval

    def processast_write(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.tokentype in (TokenType.WRITE, TokenType.WRITELN)
        tok = ast.token
        for child in ast.children:
            tmp = self.deref_ifneeded(self.processast(child))
            bt = tmp.typedef.basetype

            # p.98 of Cooper states that the constants of enumerated ordinal types (pascaltypes.EnumeratedType)
            # "don't have external character representations, and can't be read or written to or from
            # textfiles - in particular, from the standard input and output."  It would be very easy to
            # display the string representation of the constant when trying to print it out, but we will
            # stick to Cooper for now.  The ISO standard is silent on the topic, per my reading.
            if isinstance(bt, pascaltypes.SubrangeType):
                bt = bt.hosttypedef.basetype

            if not (isinstance(bt, pascaltypes.StringLiteralType) or isinstance(bt, pascaltypes.RealType) or
                    isinstance(bt, pascaltypes.BooleanType) or isinstance(bt, pascaltypes.IntegerType) or
                    isinstance(bt, pascaltypes.CharacterType) or
                    bt.is_string_type()):
                errstr = tac_errstr("Invalid type {} passed to {}".format(tmp.typedef.name, tok.value), tok)
                raise TACException(errstr)

            self.addnode(TACParamNode(tmp))
            if isinstance(bt, pascaltypes.StringLiteralType):
                self.addnode(TACCallSystemFunctionNode(Label("_WRITESL"), 1))
            elif isinstance(bt, pascaltypes.RealType):
                self.addnode(TACCallSystemFunctionNode(Label("_WRITER"), 1))
            elif isinstance(bt, pascaltypes.BooleanType):
                self.addnode(TACCallSystemFunctionNode(Label("_WRITEB"), 1))
            elif isinstance(bt, pascaltypes.IntegerType):
                self.addnode(TACCallSystemFunctionNode(Label("_WRITEI"), 1))
            elif bt.is_string_type():
                self.addnode(TACCallSystemFunctionNode(Label("_WRITEST"), 1))
            else:
                self.addnode(TACCallSystemFunctionNode(Label("_WRITEC"), 1))
        if tok.tokentype == TokenType.WRITELN:
            self.addnode(TACCallSystemFunctionNode(Label("_WRITECRLF"), 0))

    def processast_conditionalstatement(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.tokentype == TokenType.IF
        assert len(ast.children) in [2, 3], "TACBlock.processast - IF ASTs must have 2 or 3 children."

        tok = ast.token
        labeldone = self.getlabel()
        condition = self.processast(ast.children[0])
        if not isinstance(condition.typedef.basetype, pascaltypes.BooleanType):
            raise TACException("If statements must be followed by Boolean Expressions: ", tok)

        if len(ast.children) == 2:
            self.addnode(TACIFZNode(condition, labeldone))
            self.processast(ast.children[1])
            self.addnode(TACLabelNode(labeldone))
        else:
            labelelse = self.getlabel()
            self.addnode(TACIFZNode(condition, labelelse))
            self.processast(ast.children[1])
            self.addnode(TACGotoNode(labeldone))
            self.addnode(TACCommentNode("ELSE"))
            self.addnode(TACLabelNode(labelelse))
            self.processast(ast.children[2])
            self.addnode(TACLabelNode(labeldone))

    def validate_controlvariable_notthreatened(self, controlvariableidentifier, ast):
        #
        # No statement S in the ast can exist that threatens the control variable - which is defined as:
        #       a) control variable cannot be the left side (variable access) for an assignment statement
        #       b) control variable cannot be passed as a variable parameter (ByRef) to a procedure or function
        #       c) control variable cannot be passed into read() or readln()
        #       d) control variable is used as a control variable for a nested for statement (as interpreted by
        #          Cooper, p.27
        assert isinstance(ast, AST)

        if ast.token.tokentype == TokenType.ASSIGNMENT:
            if ast.children[0].token.value.lower() == controlvariableidentifier.lower():
                errstr = "Cannot assign a value to the control variable '{}' of a 'for' statement"
                errstr = errstr.format(controlvariableidentifier)
                raise TACException(tac_errstr(errstr, ast.children[0].token))
            self.validate_controlvariable_notthreatened(controlvariableidentifier, ast.children[1])
        elif ast.token.tokentype == TokenType.IDENTIFIER:
            sym = self.symboltable.fetch(ast.token.value)
            if isinstance(sym, ActivationSymbol):
                # procedure or function call - check to see if any of the parameters are the control variable
                for i in range(0, len(ast.children)):
                    child = ast.children[i]
                    if child.token.value.lower() == controlvariableidentifier.lower():
                        if sym.paramlist[i].is_byref:
                            errstr = "Cannot pass control variable '{}' of a 'for' statement as variable parameter "
                            errstr += "'{}' to '{}'"
                            errstr = errstr.format(controlvariableidentifier, sym.paramlist[i].symbol.name, sym.name)
                            raise TACException(tac_errstr(errstr, child.token))
        elif ast.token.tokentype == TokenType.FOR:
            if ast.children[0].children[0].token.value.lower() == controlvariableidentifier.lower():
                errstr = "Cannot use control variable '{}' of a 'for' statement as a control variable of a nested 'for'"
                errstr = errstr.format(controlvariableidentifier)
                raise TACException(tac_errstr(errstr, ast.children[0].children[0].token))
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
        assert ast.token.tokentype in (TokenType.REPEAT, TokenType.WHILE, TokenType.FOR)

        tok = ast.token
        if tok.tokentype == TokenType.FOR:
            assert len(ast.children) == 3, "TACBlock.processast - For SATs must have 3 children"

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
            assert todowntoast.token.tokentype in (TokenType.TO, TokenType.DOWNTO)
            assert len(todowntoast.children) == 1
            bodyast = ast.children[2]

            # need to assign the initial and final value to temp1 and temp2 so that any changes to variables
            # in the initial and final value have no impact on the for statement.  See Cooper p.28 and p.29
            initialvalue = self.processast(assignmentast.children[1])
            temp1 = Symbol(self.gettemporary(), initialvalue.location, initialvalue.typedef)
            self.symboltable.add(temp1)

            if isinstance(initialvalue, IntegerLiteral):
                self.addnode(TACUnaryLiteralNode(temp1, TACOperator.ASSIGN, initialvalue))
            else:
                self.addnode(TACUnaryNode(temp1, TACOperator.ASSIGN, initialvalue))

            finalvalue = self.processast(todowntoast.children[0])
            temp2 = Symbol(self.gettemporary(), finalvalue.location, finalvalue.typedef)
            self.symboltable.add(temp2)
            if isinstance(finalvalue, IntegerLiteral):
                self.addnode(TACUnaryLiteralNode(temp2, TACOperator.ASSIGN, finalvalue))
            else:
                self.addnode(TACUnaryNode(temp2, TACOperator.ASSIGN, finalvalue))

            controlvartoken = assignmentast.children[0].token
            assert isinstance(controlvartoken, Token)

            # Enforce rule 1 from above
            if not ast.nearest_symboltable().exists(controlvartoken.value):
                errstr = "Control variable '{}' must be declared in same block as the 'for'"
                errstr = errstr.format(controlvartoken.value)
                raise TACException(tac_errstr(errstr, controlvartoken))

            controlvarsym = self.symboltable.fetch(controlvartoken.value)
            assert isinstance(controlvarsym, Symbol)

            # Enforce rule 2 from above
            if not isinstance(controlvarsym.typedef.basetype, pascaltypes.OrdinalType):
                errstr = "'For' statements require control variables to be of ordinal type. "
                errstr += "Variable '{}' is of type '{}'".format(controlvartoken.value,
                                                                 controlvarsym.typedef.identifier)
                raise TACException(tac_errstr(errstr, controlvartoken))

            if not ast.nearest_symboltable().are_compatible(controlvarsym.typedef.identifier, temp1.typedef.identifier):
                errstr = "Type {} not compatible with type {} in 'for' statement"
                errstr = errstr.format(controlvarsym.typedef.identifier, temp1.typedef.identifier)
                raise TACException(tac_errstr(errstr, assignmentast.children[1].token))

            if not ast.nearest_symboltable().are_compatible(controlvarsym.typedef.identifier, temp2.typedef.identifier):
                errstr = "Type {} not compatible with type {} in 'for' statement"
                errstr = errstr.format(controlvarsym.typedef.identifier, temp2.typedef.identifier)
                raise TACException(tac_errstr(errstr, todowntoast.children[0].token))

            # rule 3 will be a runtime check

            # Enforce rule 4 from above
            self.validate_controlvariable_notthreatened(controlvartoken.value, bodyast)

            # finish assembling the TAC
            # TODO - refactor processast_conditionalstatement and the while from below so we don't have
            # to be repetitive

            if todowntoast.token.tokentype == TokenType.TO:
                sysfunc = Label("_SUCCO")
                compareop = TACOperator.LESSEQ
            else:
                sysfunc = Label("_PREDO")
                compareop = TACOperator.GREATEREQ

            labeldoneif = self.getlabel()
            self.addnode(TACCommentNode("If condition is true, we execute the body once."))
            ifsym = Symbol(self.gettemporary(), assignmentast.children[1].token.location,
                           pascaltypes.SIMPLETYPEDEF_BOOLEAN)
            self.symboltable.add(ifsym)
            self.addnode(TACBinaryNode(ifsym, compareop, temp1, temp2))
            self.addnode(TACIFZNode(ifsym, labeldoneif))
            self.addnode(TACUnaryNode(controlvarsym, TACOperator.ASSIGN, temp1))
            self.processast(bodyast)
            labelstartwhile = self.getlabel()
            self.addnode(TACCommentNode("The for statement now becomes a while statement"))
            self.addnode(TACLabelNode(labelstartwhile))
            whilesym = Symbol(self.gettemporary(), todowntoast.children[0].token.location,
                              pascaltypes.SIMPLETYPEDEF_BOOLEAN)
            self.symboltable.add(whilesym)
            self.addnode(TACBinaryNode(whilesym, TACOperator.NOTEQUAL, controlvarsym, temp2))
            self.addnode(TACIFZNode(whilesym, labeldoneif))
            self.addnode(TACParamNode(controlvarsym))
            self.addnode(TACCallSystemFunctionNode(sysfunc, 1, controlvarsym))
            self.processast(bodyast)
            self.addnode(TACGotoNode(labelstartwhile))
            self.addnode(TACLabelNode(labeldoneif))

        elif tok.tokentype == TokenType.WHILE:
            assert len(ast.children) == 2, "TACBlock.processast - While ASTs must have 2 children"
            labelstart = self.getlabel()
            labeldone = self.getlabel()

            self.addnode(TACLabelNode(labelstart))
            condition = self.processast(ast.children[0])
            if not isinstance(condition.typedef.basetype, pascaltypes.BooleanType):
                raise TACException("While statements must be followed by Boolean Expressions: ", tok)
            self.addnode(TACIFZNode(condition, labeldone))
            self.processast(ast.children[1])
            self.addnode(TACGotoNode(labelstart))
            self.addnode(TACLabelNode(labeldone))
        else:  # TokenType.REPEAT
            labelstart = self.getlabel()
            self.addnode(TACLabelNode(labelstart))
            maxchild = len(ast.children) - 1
            for child in ast.children[:-1]:
                self.processast(child)
            condition = self.processast(ast.children[maxchild])
            self.addnode(TACIFZNode(condition, labelstart))

    def processast_identifier(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.tokentype == TokenType.IDENTIFIER

        tok = ast.token
        if not self.symboltable.existsanywhere(tok.value):
            errstr = "Undefined Identifier: {} in {}".format(tok.value, tok.location)
            raise TACException(errstr)
        sym = self.symboltable.fetch(tok.value)
        if isinstance(sym, FunctionResultVariableSymbol):
            # need to see if it's really the result of a function, or a recursive function call
            # if it is the result of a function, the parent will be an assign and this will be the left child
            if ast.parent.token.tokentype == TokenType.ASSIGNMENT and ast.parent.children[0] == ast:
                pass
            else:
                # we know it is a function call, so get the activation symbol, which is stored in the parent
                sym = self.symboltable.parent.fetch(tok.value)

        if isinstance(sym, ConstantSymbol):
            # optimization for integers - we can just return the literal itself instead of an assignment to
            # a local symbol.
            if isinstance(sym.typedef.basetype, pascaltypes.IntegerType):
                return IntegerLiteral(sym.value, tok.location)
            else:
                ret = Symbol(self.gettemporary(), tok.location, sym.typedef)
                self.symboltable.add(ret)
                if isinstance(sym.typedef.basetype, pascaltypes.BooleanType):
                    # the value of the symbol will always be a string
                    assert sym.value.lower() in ("true", "false")
                    if sym.value.lower() == 'true':
                        tokval = "1"
                    else:
                        tokval = "0"
                    lit = BooleanLiteral(tokval, tok.location)
                elif isinstance(sym.typedef.basetype, pascaltypes.StringLiteralType):
                    lit = StringLiteral(sym.value, tok.location)
                elif isinstance(sym.typedef.basetype, pascaltypes.CharacterType):
                    lit = CharacterLiteral(sym.value, tok.location)
                elif isinstance(sym.typedef.basetype, pascaltypes.RealType):
                    lit = RealLiteral(sym.value, tok.location)
                else:
                    assert isinstance(sym.typedef.basetype, pascaltypes.EnumeratedType)
                    lit = IntegerLiteral(str(sym.typedef.basetype.position(sym.value)), tok.location)

                self.addnode(TACUnaryLiteralNode(ret, TACOperator.ASSIGN, lit))
        elif isinstance(sym, pascaltypes.EnumeratedTypeValue):
            # need to return a symbol.
            # TODO - return the enumerated type value so that we can make it a literal here instead of a symbol
            # assign.  Cannot return an IntegerLiteral here because then it will not assign properly to values
            # of the enumerated type.  Likely need an EnumeratedTypeLiteral
            tmptypedef = self.symboltable.fetch(sym.typename)
            tmpsym = Symbol(self.gettemporary(), tok.location, tmptypedef)
            self.symboltable.add(tmpsym)
            comment = "Convert literal '{}' to integer value {}".format(sym.identifier, sym.value)
            self.addnode(TACCommentNode(comment))
            self.addnode(TACUnaryLiteralNode(tmpsym, TACOperator.ASSIGN, IntegerLiteral(str(sym.value), tok.location)))
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
            if len(ast.children) != len(sym.paramlist):
                errstr = "{} expected {} parameters, but {} provided"
                errstr = errstr.format(tok.value, len(sym.paramlist.paramlist), len(ast.children))
                raise TACException(tac_errstr(errstr, tok))

            for i in range(0, len(ast.children)):
                child = ast.children[i]
                tmp = self.processast(child)

                if sym.paramlist[i].is_byref:
                    # 6.6.3.3 of the ISO Standard states that if the formal parameter is a variable
                    # parameter, then the actual parameter must be the same type as the formal parameter
                    # and the actual parameter must be a variable access, meaning it cannot be a literal
                    # or the output of a function.
                    if not isinstance(tmp, VariableSymbol):
                        errstr = "Must pass in variable for parameter {} of {}() in {}"
                        errstr = errstr.format(sym.paramlist[i].symbol.name, sym.name, child.token.location)
                        raise TACException(errstr)

                    # For variable parameters, the actual parameter must have same type as the formal parameter
                    if not ast.nearest_symboltable().are_same_type(tmp.typedef.identifier,
                                                                   sym.paramlist[i].symbol.typedef.identifier):
                        errstr = "Type Mismatch - parameter {} of {}() must be type {} in {}"
                        errstr = errstr.format(sym.paramlist[i].symbol.name, sym.name,
                                               str(sym.paramlist[i].symbol.typedef.denoter), child.token.location)
                        raise TACException(errstr)
                else:
                    # For value parameters, the actual parameter must be assignment compatible with the formal
                    # parameter
                    if not ast.nearest_symboltable().are_assignment_compatible(
                            sym.paramlist[i].symbol.typedef.identifier, tmp.typedef.identifier):
                        errstr = "Error D.7: Type Mismatch - {} is not assignment compatible with parameter"
                        errstr += "{} of {}() in {}"
                        errstr = errstr.format(tmp.typedef.denoter,
                                               sym.paramlist[i].symbol.name, sym.name, child.token.location)
                        raise TACException(errstr)

                if isinstance(tmp.typedef.basetype, pascaltypes.IntegerType) and \
                        isinstance(sym.paramlist[i].symbol.typedef.basetype, pascaltypes.RealType):
                    tmp2 = self.process_sym_inttoreal(tmp)
                    self.addnode(TACParamNode(tmp2))
                else:
                    self.addnode(TACParamNode(tmp))

            if sym.returntypedef is not None:
                # means it is a function
                ret = Symbol(self.gettemporary(), tok.location, sym.returntypedef)
                self.symboltable.add(ret)
            else:
                # procedures return nothing
                ret = None
            self.addnode(TACCallFunctionNode(sym.label, sym.name, len(ast.children), ret))

        return ret

    def processast_integerliteral(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.tokentype in (TokenType.UNSIGNED_INT, TokenType.SIGNED_INT, TokenType.MAXINT)

        tok = ast.token
        if tok.tokentype in (TokenType.UNSIGNED_INT, TokenType.SIGNED_INT):
            ret = IntegerLiteral(tok.value, tok.location)
        else:
            assert tok.tokentype == TokenType.MAXINT
            ret = IntegerLiteral(pascaltypes.STRMAXINT, tok.location)
        return ret

    def processast_realliteral(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.tokentype in (TokenType.SIGNED_REAL, TokenType.UNSIGNED_REAL)

        tok = ast.token
        lit = RealLiteral(tok.value, tok.location)
        littypedef = pascaltypes.RealLiteralTypeDef()

        ret = ConstantSymbol(self.gettemporary(), tok.location, littypedef, tok.value)
        self.symboltable.add(ret)
        self.addnode(TACUnaryLiteralNode(ret, TACOperator.ASSIGN, lit))

        return ret

    def processast_booleanliteral(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.tokentype in (TokenType.TRUE, TokenType.FALSE)

        tok = ast.token
        ret = ConstantSymbol(self.gettemporary(), tok.location, pascaltypes.SIMPLETYPEDEF_BOOLEAN, tok.value)
        self.symboltable.add(ret)
        if tok.tokentype == TokenType.TRUE:
            tokval = "1"  # 6.4.2.2 of ISO standard - Booleans are stored as 0 or 1 in memory
        else:
            tokval = "0"
        self.addnode(TACUnaryLiteralNode(ret, TACOperator.ASSIGN, BooleanLiteral(tokval, tok.location)))
        return ret

    def processast_characterstring(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.tokentype == TokenType.CHARSTRING

        tok = ast.token

        litval = tok.value
        # string of length 1 is a character.  String of any other length is a string literal
        if len(litval) != 1:
            littypedef = pascaltypes.StringLiteralTypeDef()
            lit = StringLiteral(litval, tok.location)
        else:
            littypedef = pascaltypes.SIMPLETYPEDEF_CHAR
            lit = CharacterLiteral(litval, tok.location)

        ret = ConstantSymbol(self.gettemporary(), tok.location, littypedef, litval)
        self.symboltable.add(ret)
        self.addnode(TACUnaryLiteralNode(ret, TACOperator.ASSIGN, lit))
        return ret

    def processast_array(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.tokentype == TokenType.LBRACKET
        assert len(ast.children) == 2, "TACBlock.processast_array - Array ASTs must have 2 children."

        '''
        Core Logic:
            Step 1 - resolve the lval.  It will either be a symbol with a typedef of an array, or a 
            pointer, that points to the typedef of an array.
            
            Step 2 - create a symbol that is a pointer that points to the lval array's component type.
            If the lval is an array symbol, set lval to the address of the array.  If the lval is 
            already a pointer, then set this symbol equal to the lval.
            
            Step 3 - grab the result of the index expression
            
            Step 4 - compute the size of the component type of the array.  Take the result of step 3,
            subtract the index minimum of the array from that, and then multiply it by the size of the
            component type.  If the result of step 3 is a literal, we can do the math in the compiler.
            If the result of step 3 is a symbol, then we need to do the math at runtime.
            
            Step 5 - add the number of bytes result from step 4, add that to the address of the pointer
            in step 2, and store that result in a symbol.  The typedef for the symbol should equal
            a pointer to the componenttypedef for the array.  Return this symbol.
        '''

        step1 = self.processast(ast.children[0])
        assert isinstance(step1.typedef, pascaltypes.ArrayTypeDef) or \
            (isinstance(step1.typedef, pascaltypes.PointerTypeDef) and
             isinstance(step1.typedef.pointsto_typedef, pascaltypes.ArrayTypeDef))
        
        if isinstance(step1.typedef, pascaltypes.ArrayTypeDef):
            arraytypedef = step1.typedef
            componenttypedef = arraytypedef.basetype.componenttypedef
            indextypedef = arraytypedef.basetype.indextypedef
            assignop = TACOperator.ASSIGNADDRESSOF
        else:
            arraytypedef = step1.typedef.pointsto_typedef
            assert isinstance(arraytypedef, pascaltypes.ArrayTypeDef)
            componenttypedef = arraytypedef.basetype.componenttypedef
            indextypedef = arraytypedef.basetype.indextypedef
            assignop = TACOperator.ASSIGN

        step2 = Symbol(self.gettemporary(), step1.location, componenttypedef.get_pointer_to())
        self.symboltable.add(step2)
        self.addnode(TACUnaryNode(step2, assignop, step1))

        step3 = self.deref_ifneeded(self.processast(ast.children[1]))

        # the type of the index expression must be assignment compatible with the index type
        # (Cooper p.115)
        if not self.symboltable.are_assignment_compatible(indextypedef.identifier, step3.typedef.identifier):
            # Error D.1 comes from 6.5.3.2 of the ISO standard
            raise TACException("Error D.1: Incorrect type for array index in {}".format(ast.children[1].token.location))

        # logic here - take result of (step 3 minus the minimum index) and multiply by the component size.
        # add that to the result of step 2.

        # TODO - if the array is an enumerated type (and possibly an ordinal type like char) it will not have
        # a subrange.
        if isinstance(indextypedef.basetype, pascaltypes.SubrangeType):
            minrange = indextypedef.basetype.rangemin_int
            maxrange = indextypedef.basetype.rangemax_int
        else:
            assert isinstance(indextypedef.basetype, pascaltypes.OrdinalType)
            if isinstance(indextypedef.basetype, pascaltypes.IntegerType):
                raise TACException("Cannot have an array with index range 'integer' in {}".format(ast.token.location))
            minrange = indextypedef.basetype.position(indextypedef.basetype.min_item())
            maxrange = indextypedef.basetype.position(indextypedef.basetype.max_item())

        if isinstance(step3, IntegerLiteral):
            # we can do the math in the compiler
            if int(step3.value) < minrange or int(step3.value) > maxrange:
                errstr = "Array Index '{}' out of range in: {}".format(step3.value, step3.location)
                raise TACException(errstr)

            indexpos = (int(step3.value) - minrange)
            numbytes = indexpos * componenttypedef.basetype.size
            step4 = IntegerLiteral(str(numbytes), step1.location)
        else:
            step4a = Symbol(self.gettemporary(), step1.location, pascaltypes.SIMPLETYPEDEF_INTEGER)
            indexmin_literal = IntegerLiteral(str(minrange), step1.location)
            size_literal = IntegerLiteral(str(componenttypedef.basetype.size), step1.location)
            self.symboltable.add(step4a)
            self.addnode(TACBinaryNode(step4a, TACOperator.SUBTRACT, step3, indexmin_literal))
            step4 = Symbol(self.gettemporary(), step1.location, pascaltypes.SIMPLETYPEDEF_INTEGER)
            self.symboltable.add(step4)
            self.addnode(TACBinaryNode(step4, TACOperator.MULTIPLY, step4a, size_literal))

        step5 = Symbol(self.gettemporary(), step1.location, step2.typedef)
        self.symboltable.add(step5)

        self.addnode(TACBinaryNodeWithBoundsCheck(step5, TACOperator.ADD, step2, step4, 0,
                                                  arraytypedef.basetype.size-1))
        return step5

    def processast_assignment(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.tokentype == TokenType.ASSIGNMENT
        assert len(ast.children) == 2, "TACBlock.processast_assignment - Assignment ASTs must have 2 children."

        lval = self.processast(ast.children[0])
        if isinstance(lval.typedef, pascaltypes.PointerTypeDef):
            lval_reftypedef = lval.typedef.pointsto_typedef
            assignop = TACOperator.ASSIGNTODEREF
        else:
            lval_reftypedef = lval.typedef
            assignop = TACOperator.ASSIGN

        if isinstance(lval, ConstantSymbol):
            raise TACException(tac_errstr("Cannot assign a value to a constant", ast.token))

        rval = self.deref_ifneeded(self.processast(ast.children[1]))

        if isinstance(rval, pascaltypes.EnumeratedTypeValue):
            comment = "Convert literal {} to integer value {}".format(rval.identifier, rval.value)
            self.addnode(TACCommentNode(comment))
            self.addnode(TACUnaryLiteralNode(lval, TACOperator.ASSIGN,
                                             IntegerLiteral(str(rval.value), ast.children[1].token.location)))
        else:
            if isinstance(rval, ConstantSymbol) or isinstance(rval, IntegerLiteral):
                t2value = rval.value
            else:
                t2value = None

            if not ast.nearest_symboltable().are_assignment_compatible(lval_reftypedef.identifier,
                                                                       rval.typedef.identifier, t2value):
                if t2value is not None:
                    errstr = "Cannot assign value '{}' of type {} to type {}"
                    if isinstance(rval.typedef.basetype, pascaltypes.OrdinalType):
                        # the error in 6.8.2.2 is specific to ordinal types.
                        errstr = "Error D.49: " + errstr
                    errstr = errstr.format(t2value, rval.typedef.identifier, lval_reftypedef.identifier)
                else:
                    errstr = "Cannot assign {} type to {}".format(rval.typedef.identifier, lval_reftypedef.identifier)
                raise TACException(tac_errstr(errstr, ast.children[1].token))
            if isinstance(lval_reftypedef.basetype, pascaltypes.RealType) and \
                    isinstance(rval.typedef.basetype, pascaltypes.IntegerType):
                newrval = self.process_sym_inttoreal(rval)
            else:
                newrval = rval

            if isinstance(newrval, Literal):
                self.addnode(TACUnaryLiteralNode(lval, assignop, newrval))
            else:
                self.addnode(TACUnaryNode(lval, assignop, newrval))
        return lval

    def process_sym_inttoreal(self, sym):
        # sym is a symbol of integer type.  Returns a symbol that converts tok to a real type
        assert isinstance(sym, Symbol) or isinstance(sym, IntegerLiteral)
        if isinstance(sym, Symbol):
            assert isinstance(sym.typedef.basetype, pascaltypes.IntegerType)
        ret = Symbol(self.gettemporary(), sym.location, pascaltypes.SIMPLETYPEDEF_REAL)
        self.symboltable.add(ret)
        if isinstance(sym, Symbol):
            self.addnode(TACUnaryNode(ret, TACOperator.INTTOREAL, sym))
        else:
            self.addnode(TACUnaryLiteralNode(ret, TACOperator.INTTOREAL, sym))
        return ret

    def processast_arithmeticoperator(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.tokentype in (TokenType.MULTIPLY, TokenType.PLUS, TokenType.MINUS, TokenType.DIVIDE,
                                       TokenType.IDIV, TokenType.MOD)
        assert len(ast.children) == 2

        tok = ast.token
        op = maptokentype_to_tacoperator(tok.tokentype)
        child1 = self.deref_ifneeded(self.processast(ast.children[0]))
        child2 = self.deref_ifneeded(self.processast(ast.children[1]))

        if isinstance(child1.typedef.basetype, pascaltypes.BooleanType) or \
                isinstance(child2.typedef.basetype, pascaltypes.BooleanType):
            raise TACException(tac_errstr("Cannot use boolean type with math operators", tok))

        if tok.tokentype in (TokenType.IDIV, TokenType.MOD) and \
                (isinstance(child1.typedef.basetype, pascaltypes.RealType) or
                 isinstance(child2.typedef.basetype, pascaltypes.RealType)):
            raise TACException(tac_errstr("Cannot use integer division with Real values.", tok))

        # The addition, subtraction, multiplication operators can take integers or reals, and return
        # integer if both operands are integers, or a real if one or both operands are reals.  The
        # division operator returns a real even if both operands are integers
        if isinstance(child1.typedef.basetype, pascaltypes.RealType) or \
                isinstance(child2.typedef.basetype, pascaltypes.RealType) or \
                op == TACOperator.DIVIDE:

            # 6.7.2.1 of the ISO Standard states that if either operand of addition, subtraction, or multiplication
            # are real-type, then the result will also be real-type.  Similarly, if the "/" operator is used,
            # even if both operands are integer-type, the result is real-type.  Cooper states on p.31 that
            # "[t]his means that integer operands are sometimes coerced into being reals; i.e. they are temporarily
            # treated as values of type real."
            if isinstance(child1.typedef.basetype, pascaltypes.IntegerType):
                newchild1 = self.process_sym_inttoreal(child1)
            else:
                newchild1 = child1

            if isinstance(child2.typedef.basetype, pascaltypes.IntegerType):
                newchild2 = self.process_sym_inttoreal(child2)
            else:
                newchild2 = child2

            ret = Symbol(self.gettemporary(), tok.location, pascaltypes.SIMPLETYPEDEF_REAL)
            self.symboltable.add(ret)
            self.addnode(TACBinaryNode(ret, op, newchild1, newchild2))
        else:
            ret = Symbol(self.gettemporary(), tok.location, pascaltypes.SIMPLETYPEDEF_INTEGER)
            self.symboltable.add(ret)
            self.addnode(TACBinaryNode(ret, op, child1, child2))

        return ret

    def processast_relationaloperator(self, ast):
        assert isinstance(ast, AST)
        assert isrelationaloperator(ast.token.tokentype)

        tok = ast.token
        op = maptokentype_to_tacoperator(tok.tokentype)
        child1 = self.deref_ifneeded(self.processast(ast.children[0]))
        child2 = self.deref_ifneeded(self.processast(ast.children[1]))

        c1type = child1.typedef.basetype
        c2type = child2.typedef.basetype

        # 6.7.2.5 of the ISO standard says that the operands of relational operators shall be of compatible
        # types, or one operand shall be of real-type and the other of integer-type.  Table 6, has
        # simple-types, pointer-types, and string-types allowed in the comparisons..

        if not self.symboltable.are_compatible(child1.typedef.identifier, child2.typedef.identifier):
            if isinstance(c1type, pascaltypes.IntegerType) and isinstance(c2type, pascaltypes.RealType):
                pass
            elif isinstance(c2type, pascaltypes.IntegerType) and isinstance(c1type, pascaltypes.RealType):
                pass
            elif isinstance(c1type, pascaltypes.BooleanType) or isinstance(c2type, pascaltypes.BooleanType):
                raise TACException(tac_errstr("Cannot compare Boolean to non-Boolean", tok))
            else:
                errstr = "Cannot compare types '{}' and '{}' with relational operator"
                errstr = errstr.format(child1.typedef.identifier, child2.typedef.identifier)
                raise TACException(tac_errstr(errstr, tok))

        if isinstance(c1type, pascaltypes.IntegerType) and isinstance(c2type, pascaltypes.RealType):
            newchild1 = self.process_sym_inttoreal(child1)
        else:
            newchild1 = child1
        if isinstance(c2type, pascaltypes.IntegerType) and isinstance(c1type, pascaltypes.RealType):
            newchild2 = self.process_sym_inttoreal(child2)
        else:
            newchild2 = child2

        ret = Symbol(self.gettemporary(), tok.location, pascaltypes.SIMPLETYPEDEF_BOOLEAN)
        self.symboltable.add(ret)
        self.addnode(TACBinaryNode(ret, op, newchild1, newchild2))
        return ret

    def processast_booleanoperator(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.tokentype in (TokenType.AND, TokenType.OR, TokenType.NOT)

        tok = ast.token
        op = maptokentype_to_tacoperator(tok.tokentype)

        if tok.tokentype in (TokenType.AND, TokenType.OR):
            child1 = self.deref_ifneeded(self.processast(ast.children[0]))
            child2 = self.deref_ifneeded(self.processast(ast.children[1]))
            if not isinstance(child1.typedef.basetype, pascaltypes.BooleanType) or \
                    not isinstance(child2.typedef.basetype, pascaltypes.BooleanType):
                errstr = "Both arguments to operator '{}' must be Boolean type".format(tok.value)
                raise TACException(tac_errstr(errstr, tok))
            ret = Symbol(self.gettemporary(), tok.location, pascaltypes.SIMPLETYPEDEF_BOOLEAN)
            self.symboltable.add(ret)
            self.addnode(TACBinaryNode(ret, op, child1, child2))
        else:  # tok.tokentype == TokenType.NOT
            child = self.deref_ifneeded(self.processast(ast.children[0]))
            if not isinstance(child.typedef.basetype, pascaltypes.BooleanType):
                raise TACException(tac_errstr("Operator 'not' can only be applied to Boolean factors", tok))
            ret = Symbol(self.gettemporary(), tok.location, pascaltypes.SIMPLETYPEDEF_BOOLEAN)
            self.symboltable.add(ret)
            self.addnode(TACUnaryNode(ret, op, child))
        return ret

    def processast(self, ast):
        """ returns the Symbol of a temporary that holds the result of this computation, or None """

        assert isinstance(ast, AST)
        if ast.comment != "":
            self.addnode(TACCommentNode(ast.comment))

        tok = ast.token
        toktype = ast.token.tokentype

        # Begin statements, Procedure/Function declarations, Output, Conditionals, and Repetitive statements
        # do not return anything.  Identifiers generally do, unless they are procedure calls.  Everything else
        # returns a symbol.

        ret = None

        if toktype == TokenType.BEGIN:
            self.processast_begin(ast)
        elif toktype in (TokenType.PROCEDURE, TokenType.FUNCTION):
            self.processast_procedurefunction(ast)
        elif toktype in (TokenType.WRITE, TokenType.WRITELN):
            self.processast_write(ast)
        elif toktype == TokenType.IF:
            self.processast_conditionalstatement(ast)
        elif toktype in (TokenType.WHILE, TokenType.REPEAT, TokenType.FOR):
            self.processast_repetitivestatement(ast)
        elif is_isorequiredfunction(tok.tokentype):
            ret = self.processast_isorequiredfunction(ast)
        elif toktype == TokenType.LBRACKET:
            ret = self.processast_array(ast)
        elif toktype == TokenType.ASSIGNMENT:
            ret = self.processast_assignment(ast)
        elif toktype == TokenType.IDENTIFIER:
            ret = self.processast_identifier(ast)
        elif tok.tokentype in (TokenType.UNSIGNED_INT, TokenType.SIGNED_INT, TokenType.MAXINT):
            ret = self.processast_integerliteral(ast)
        elif tok.tokentype in (TokenType.UNSIGNED_REAL, TokenType.SIGNED_REAL):
            ret = self.processast_realliteral(ast)
        elif tok.tokentype in [TokenType.TRUE, TokenType.FALSE]:
            ret = self.processast_booleanliteral(ast)
        elif tok.tokentype == TokenType.CHARSTRING:
            ret = self.processast_characterstring(ast)
        elif tok.tokentype in (TokenType.MULTIPLY, TokenType.PLUS, TokenType.MINUS, TokenType.DIVIDE,
                               TokenType.IDIV, TokenType.MOD):
            ret = self.processast_arithmeticoperator(ast)
        elif isrelationaloperator(tok.tokentype):
            ret = self.processast_relationaloperator(ast)
        elif tok.tokentype in (TokenType.AND, TokenType.OR, TokenType.NOT):
            ret = self.processast_booleanoperator(ast)
        else:  # pragma: no cover
            raise TACException("TACBlock.processast - cannot process token:", str(tok))

        assert ret is None or isinstance(ret, Symbol) or isinstance(ret, IntegerLiteral)
        return ret


class TACGenerator:
    def __init__(self, literaltable):
        assert isinstance(literaltable, LiteralTable)
        self.tacblocks = []
        self.nextlabel = 0
        self.nexttemporary = 0
        self.nextanonymoustype = 0
        self.globalsymboltable = SymbolTable()
        self.globalliteraltable = deepcopy(literaltable)

    def addblock(self, block):
        assert isinstance(block, TACBlock)
        self.tacblocks.append(block)

    def generateblock(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.tokentype in (TokenType.BEGIN, TokenType.PROCEDURE, TokenType.FUNCTION)
        # process the main begin
        if ast.token.tokentype == TokenType.BEGIN:
            newblock = TACBlock(True, self)
        else:
            newblock = TACBlock(False, self)
            newblock.symboltable = deepcopy(ast.symboltable)
        newblock.symboltable.parent = self.globalsymboltable
        newblock.processast(ast)
        return newblock

    def generate(self, ast):
        assert isinstance(ast, AST)
        assert ast.token.tokentype == TokenType.PROGRAM
        self.globalsymboltable = deepcopy(ast.symboltable)
        for child in ast.children:
            self.addblock(self.generateblock(child))
        # insure there is exactly one main block
        mainblockcount = 0
        for block in self.tacblocks:
            if block.ismain:
                mainblockcount += 1
        assert(mainblockcount == 1), \
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

    def gettypetemporary(self):
        temporary = "_TYPE_" + str(self.nextanonymoustype)
        self.nextanonymoustype += 1
        return temporary

    def printblocks(self):
        for block in self.tacblocks:
            if block.ismain:
                print("_MAIN:")
            block.printnodes()
