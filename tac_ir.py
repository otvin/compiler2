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
        Array References
        Read/Readln from console
        Read/Write from/to files
"""

from enum import Enum, unique
from copy import deepcopy
from parser import AST, isrelationaloperator
from symboltable import Symbol, Label, Literal, NumericLiteral, StringLiteral, BooleanLiteral,\
    SymbolTable, LiteralTable, ParameterList, ActivationSymbol, Parameter, VariableSymbol,\
    FunctionResultVariableSymbol
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
    elif tokentype == TokenType.DIVIDE:
        ret = TACOperator.DIVIDE
    else:
        raise ValueError("Unable to map tokentype {} to TACOperator.".format(tokentype))
    return ret


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
    def __init__(self, label, paramlist, returntype=None):
        super().__init__(label)
        assert isinstance(paramlist, ParameterList)
        self.paramlist = paramlist
        assert returntype is None or isinstance(returntype, pascaltypes.OrdinalType)

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
        assert isinstance(paramval, Symbol)
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
            return "{} := {} {} {}".format(str(self.lval), str(self.operator),
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
        litval = ""
        if isinstance(self.literal1, NumericLiteral) or isinstance(self.literal1, BooleanLiteral):
            litval = str(self.literal1)
        elif isinstance(self.literal1, StringLiteral):
            litval = '"{}"'.format(str(self.literal1).replace('"', '\"'))
        return "{} {} {}".format(str(self.lval), str(self.operator), litval)


# TODO if there is something other than T0 := T1 <oper> T2 then need to pass in the first operator too
class TACBinaryNode(TACNode):
    def __init__(self, result, operator, arg1, arg2):
        assert isinstance(result, Symbol)
        assert isinstance(arg1, Symbol)
        assert isinstance(arg2, Symbol)
        super().__init__(operator)
        self.result = result
        self.arg1 = arg1
        self.arg2 = arg2

    def __str__(self):
        return "{} := {} {} {}".format(str(self.result), str(self.arg1), str(self.operator), str(self.arg2))


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


"""
class TACBinaryNodeLiteralLeft(TACNode):
    def __init__(self, result, operator, literal1, arg2):
        assert isinstance(result, Symbol)
        assert isinstance(literal1, Literal)
        assert isinstance(arg2, Symbol)
        super().__init__(operator)
        self.result = result
        self.literal1 = literal1
        self.arg2 = arg2


class TACBinaryNodeLiteralRight(TACNode):
    def __init__(self, result, operator, arg1, literal2):
        assert isinstance(result, Symbol)
        assert isinstance(arg1, Symbol)
        assert isinstance(literal2, Literal)
        super().__init__(operator)
        self.result = result
        self.arg1 = arg1
        self.literal2 = literal2
"""


class TACBlock:
    """ For now, assume a TACBlock represents a Pascal Block.  Not entirely language-independent but
    will work.

    NOTE: For it really to be a Pascal block, we will need to have TACBlocks within TACBlocks when
    we allow procedures and functions to be declared within another procedure or function.  This
    could in theory be done with a TACNode that contains a TACBlock?  Need to figure that out later.
    """
    def __init__(self, ismain):
        assert isinstance(ismain, bool)
        self.ismain = ismain
        self.tacnodes = []
        self.symboltable = SymbolTable()
        self.paramlist = None

    def addnode(self, node):
        assert isinstance(node, TACNode)
        self.tacnodes.append(node)

    def printnodes(self):
        for node in self.tacnodes:
            print(str(node))

    # TODO - fix passing the generator around like this it's ugly
    def processast(self, ast, generator):
        """ returns the Symbol of a temporary that holds the result of this computation, or None """

        assert isinstance(ast, AST)
        assert isinstance(generator, TACGenerator)
        if ast.comment != "":
            self.addnode(TACCommentNode(ast.comment))
        tok = ast.token
        if tok.tokentype == TokenType.BEGIN:
            for child in ast.children:
                self.processast(child, generator)
            return None
        elif tok.tokentype in (TokenType.PROCEDURE, TokenType.FUNCTION):
            # TODO - when we want to have procedures declared within procedures, this next line will fail.
            # For now, we're ensuring the Procedure/Function is the first TACNode in the list.  This
            # matters because we are going to copy the parameter list from the AST to the TACBlock
            # and cannot do that if we have multiple parameter lists for nested procs.
            # We need some other structure.
            assert len(self.tacnodes) == 0

            # first child of a Procedure or Function is an identifier with the name of the proc/func
            assert len(ast.children) >= 1
            assert ast.children[0].token.tokentype == TokenType.IDENTIFIER
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
            proclabel = generator.getlabel(str_procname)
            actsym.label = proclabel
            if tok.tokentype == TokenType.FUNCTION:
                comment = "Function {}({})".format(str_procname, str(self.paramlist))
            else:
                comment = "Procedure {}({})".format(str_procname, str(self.paramlist))
            self.addnode(TACLabelNode(proclabel, comment))

            for child in ast.children[1:]:
                self.processast(child, generator)

            if tok.tokentype == TokenType.FUNCTION:
                self.addnode(TACFunctionReturnNode(self.symboltable.fetch(str_procname)))
            else:
                self.addnode(TACFunctionReturnNode(None))

        elif tok.tokentype in (TokenType.WRITE, TokenType.WRITELN):
            for child in ast.children:
                # TODO - if child is a procedure, not a function, we should have a compile error here.
                tmp = self.processast(child, generator)
                self.addnode(TACParamNode(tmp))
                if isinstance(tmp.pascaltype, pascaltypes.StringLiteralType):
                    self.addnode(TACCallSystemFunctionNode(Label("_WRITES"), 1))
                elif isinstance(tmp.pascaltype, pascaltypes.RealType):
                    self.addnode(TACCallSystemFunctionNode(Label("_WRITER"), 1))
                elif isinstance(tmp.pascaltype, pascaltypes.BooleanType):
                    self.addnode(TACCallSystemFunctionNode(Label("_WRITEB"), 1))
                else:
                    self.addnode(TACCallSystemFunctionNode(Label("_WRITEI"), 1))
            if tok.tokentype == TokenType.WRITELN:
                self.addnode(TACCallSystemFunctionNode(Label("_WRITECRLF"), 0))
            return None
        elif tok.tokentype == TokenType.IF:
            assert len(ast.children) in [2, 3], "TACBlock.processast - IF ASTs must have 2 or 3 children."
            labeldone = generator.getlabel()
            condition = self.processast(ast.children[0], generator)
            if not isinstance(condition.pascaltype, pascaltypes.BooleanType):
                raise TACException("If statements must be followed by Boolean Expressions: ", tok)

            if len(ast.children) == 2:
                self.addnode(TACIFZNode(condition, labeldone))
                self.processast(ast.children[1], generator)
                self.addnode(TACLabelNode(labeldone))
            else:
                labelelse = generator.getlabel()
                self.addnode(TACIFZNode(condition, labelelse))
                self.processast(ast.children[1], generator)
                self.addnode(TACGotoNode(labeldone))
                self.addnode(TACCommentNode("ELSE"))
                self.addnode(TACLabelNode(labelelse))
                self.processast(ast.children[2], generator)
                self.addnode(TACLabelNode(labeldone))
            return None
        elif tok.tokentype == TokenType.WHILE:
            assert len(ast.children) == 2, "TACBlock.processast - While ASTs must have 2 children"
            labelstart = generator.getlabel()
            labeldone = generator.getlabel()

            self.addnode(TACLabelNode(labelstart))
            condition = self.processast(ast.children[0], generator)
            if not isinstance(condition.pascaltype, pascaltypes.BooleanType):
                raise TACException("While statements must be followed by Boolean Expressions: ", tok)
            self.addnode(TACIFZNode(condition, labeldone))
            self.processast(ast.children[1], generator)
            self.addnode(TACGotoNode(labelstart))
            self.addnode(TACLabelNode(labeldone))
        elif tok.tokentype == TokenType.REPEAT:
            labelstart = generator.getlabel()
            self.addnode(TACLabelNode(labelstart))
            maxchild = len(ast.children) - 1
            # TODO - there is a more pythonic way to do this, but I cannot look it up now
            i = 0
            while i < maxchild:
                self.processast(ast.children[i], generator)
                i += 1
            condition = self.processast(ast.children[maxchild], generator)
            self.addnode(TACIFZNode(condition, labelstart))
        elif tok.tokentype == TokenType.ASSIGNMENT:
            assert len(ast.children) == 2, "TACBlock.processast - Assignment ASTs must have 2 children."
            lval = self.symboltable.fetch(ast.children[0].token.value)
            rval = self.processast(ast.children[1], generator)
            if isinstance(lval.pascaltype, pascaltypes.RealType) and\
                    isinstance(rval.pascaltype, pascaltypes.IntegerType):
                newrval = Symbol(generator.gettemporary(), tok.location, pascaltypes.RealType())
                self.symboltable.add(newrval)
                self.addnode(TACUnaryNode(newrval, TACOperator.INTTOREAL, rval))
            elif isinstance(lval.pascaltype, pascaltypes.IntegerType) and\
                    isinstance(rval.pascaltype, pascaltypes.RealType):
                raise TACException(tac_errstr("Cannot assign real type to integer", tok))
            else:
                newrval = rval
            self.addnode(TACUnaryNode(lval, TACOperator.ASSIGN, newrval))
            return lval
        elif tok.tokentype == TokenType.IDENTIFIER:
            sym = self.symboltable.fetch(tok.value)
            if isinstance(sym, FunctionResultVariableSymbol):
                # we know it is a function, so get the activation symbol, which is stored in the parent
                sym = self.symboltable.parent.fetch(tok.value)
            if isinstance(sym, ActivationSymbol):
                # children of the AST node are the parameters to the proc/func.  Validate count is correct
                if len(ast.children) != len(sym.paramlist):
                    errstr = "{} expected {} parameters, but {} provided"
                    errstr = errstr.format(tok.value, len(sym.paramlist.paramlist), len(ast.children))
                    raise TACException(tac_errstr(errstr, tok))

                for i in range(0, len(ast.children)):
                    child = ast.children[i]
                    # TODO - check type of the parameters for a match, more than just real vs. int
                    tmp = self.processast(child, generator)

                    if sym.paramlist[i].is_byref:
                        # 6.6.3.3 of the ISO Standard states that if the formal parameter is a variable
                        # parameter, then the actual parameter must be the same type as the formal parameter
                        # and the actual parameter must be a variable access, meaning it cannot be a literal
                        # or the output of a function.
                        if not isinstance(tmp, VariableSymbol):
                            errstr = "Must pass in variable for parameter {} of {}() in {}"
                            errstr = errstr.format(sym.paramlist[i].symbol.name, sym.name, child.token.location)
                            raise TACException(errstr)
                        # Known PEP-8 violation here - but I don't know how else to compare the types
                        # without creating a canonical example of each type and then using that everywhere in the
                        # compiler.
                        if type(tmp.pascaltype) != type(sym.paramlist[i].symbol.pascaltype):
                            errstr = "Type Mismatch - parameter {} of {}() must be type {} in {}"
                            errstr = errstr.format(sym.paramlist[i].symbol.name, sym.name,
                                                   str(sym.paramlist[i].symbol.pascaltype), child.token.location)
                            raise TACException(errstr)

                    if isinstance(tmp.pascaltype, pascaltypes.IntegerType) and \
                            isinstance(sym.paramlist[i].symbol.pascaltype, pascaltypes.RealType):
                        tmp2 = Symbol(generator.gettemporary(), tok.location, pascaltypes.RealType())
                        self.symboltable.add(tmp2)
                        self.addnode(TACUnaryNode(tmp2, TACOperator.INTTOREAL, tmp))
                        self.addnode(TACParamNode(tmp2))
                    else:
                        self.addnode(TACParamNode(tmp))
                if sym.returnpascaltype is not None:
                    # means it is a function
                    ret = Symbol(generator.gettemporary(), tok.location, sym.returnpascaltype)
                    self.symboltable.add(ret)
                else:
                    ret = None
                self.addnode(TACCallFunctionNode(sym.label, sym.name, len(ast.children), ret))
                return ret
            else:
                return sym
        elif tok.tokentype in [TokenType.UNSIGNED_INT, TokenType.SIGNED_INT]:
            ret = Symbol(generator.gettemporary(), tok.location, pascaltypes.IntegerType())
            self.symboltable.add(ret)
            self.addnode(TACUnaryLiteralNode(ret, TACOperator.ASSIGN,
                                             NumericLiteral(tok.value, tok.location, pascaltypes.IntegerType())))
            return ret
        elif tok.tokentype in [TokenType.UNSIGNED_REAL, TokenType.SIGNED_REAL]:
            ret = Symbol(generator.gettemporary(), tok.location, pascaltypes.RealType())
            self.symboltable.add(ret)
            self.addnode(TACUnaryLiteralNode(ret, TACOperator.ASSIGN,
                                             NumericLiteral(tok.value, tok.location, pascaltypes.RealType())))
            return ret
        elif tok.tokentype in [TokenType.TRUE, TokenType.FALSE]:
            ret = Symbol(generator.gettemporary(), tok.location, pascaltypes.BooleanType())
            self.symboltable.add(ret)
            if tok.tokentype == TokenType.TRUE:
                tokval = 1  # 6.4.2.2 of ISO standard - Booleans are stored as 0 or 1 in memory
            else:
                tokval = 0
            self.addnode(TACUnaryLiteralNode(ret, TACOperator.ASSIGN, BooleanLiteral(tokval, tok.location)))
            return ret
        elif tok.tokentype == TokenType.CHARSTRING:
            ret = Symbol(generator.gettemporary(), tok.location, pascaltypes.StringLiteralType())
            self.symboltable.add(ret)
            self.addnode(TACUnaryLiteralNode(ret, TACOperator.ASSIGN, StringLiteral(tok.value, tok.location)))
            return ret
        elif tok.tokentype in (TokenType.MULTIPLY, TokenType.PLUS, TokenType.MINUS, TokenType.DIVIDE):
            op = maptokentype_to_tacoperator(tok.tokentype)
            child1 = self.processast(ast.children[0], generator)
            child2 = self.processast(ast.children[1], generator)

            if isinstance(child1.pascaltype, pascaltypes.BooleanType) or\
                    isinstance(child2.pascaltype, pascaltypes.BooleanType):
                raise ValueError("Cannot use boolean type with math operators")

            if isinstance(child1.pascaltype, pascaltypes.RealType) or\
                    isinstance(child2.pascaltype, pascaltypes.RealType) or\
                    op == TACOperator.DIVIDE:
                # 6.7.2.1 of the ISO Standard states that if either operand of addition, subtraction, or multiplication
                # are real-type, then the result will also be real-type.  Similarly, if the "/" operator is used,
                # even if both operands are integer-type, the result is real-type.  Cooper states on p.31 that
                # "[t]his means that integer operands are sometimes coerced into being reals; i.e. they are temporarily
                # treated as values of type real."
                if isinstance(child1.pascaltype, pascaltypes.IntegerType):
                    newchild1 = Symbol(generator.gettemporary(), tok.location, pascaltypes.RealType())
                    self.symboltable.add(newchild1)
                    self.addnode(TACUnaryNode(newchild1, TACOperator.INTTOREAL, child1))
                else:
                    newchild1 = child1

                if isinstance(child2.pascaltype, pascaltypes.IntegerType):
                    newchild2 = Symbol(generator.gettemporary(), tok.location, pascaltypes.RealType())
                    self.symboltable.add(newchild2)
                    self.addnode(TACUnaryNode(newchild2, TACOperator.INTTOREAL, child2))
                else:
                    newchild2 = child2

                ret = Symbol(generator.gettemporary(), tok.location, pascaltypes.RealType())
                self.symboltable.add(ret)
                self.addnode(TACBinaryNode(ret, op, newchild1, newchild2))
            else:
                ret = Symbol(generator.gettemporary(), tok.location, pascaltypes.IntegerType())
                self.symboltable.add(ret)
                self.addnode(TACBinaryNode(ret, op, child1, child2))
            return ret
        elif tok.tokentype in (TokenType.IDIV, TokenType.MOD):
            op = maptokentype_to_tacoperator(tok.tokentype)
            child1 = self.processast(ast.children[0], generator)
            child2 = self.processast(ast.children[1], generator)
            if isinstance(child1.pascaltype, pascaltypes.RealType) or\
                    isinstance(child2.pascaltype, pascaltypes.RealType):
                raise ValueError("Cannot use integer division with Real values.")
            if isinstance(child1.pascaltype, pascaltypes.BooleanType) or \
                    isinstance(child2.pascaltype, pascaltypes.BooleanType):
                raise ValueError("Cannot use integer division with Boolean values.")
            ret = Symbol(generator.gettemporary(), tok.location, pascaltypes.IntegerType())
            self.symboltable.add(ret)
            self.addnode(TACBinaryNode(ret, op, child1, child2))
            return ret
        elif isrelationaloperator(tok.tokentype):
            op = maptokentype_to_tacoperator(tok.tokentype)
            child1 = self.processast(ast.children[0], generator)
            child2 = self.processast(ast.children[1], generator)

            c1type = child1.pascaltype
            c2type = child2.pascaltype

            if isinstance(c1type, pascaltypes.BooleanType) and not isinstance(c2type, pascaltypes.BooleanType):
                raise TACException(tac_errstr("Cannot compare Boolean to non-Boolean", tok))
            if isinstance(c2type, pascaltypes.BooleanType) and not isinstance(c1type, pascaltypes.BooleanType):
                raise TACException(tac_errstr("Cannot compare Boolean to non-Boolean", tok))
            if isinstance(c1type, pascaltypes.IntegerType) and isinstance(c2type, pascaltypes.RealType):
                newchild1 = Symbol(generator.gettemporary(), tok.location, pascaltypes.RealType())
                self.symboltable.add(newchild1)
                self.addnode(TACUnaryNode(newchild1, TACOperator.INTTOREAL, child1))
            else:
                newchild1 = child1
            if isinstance(c2type, pascaltypes.IntegerType) and isinstance(c1type, pascaltypes.RealType):
                # TODO - this newchild pattern is coming up lots of times, should refactor it
                newchild2 = Symbol(generator.gettemporary(), tok.location, pascaltypes.RealType())
                self.symboltable.add(newchild2)
                self.addnode(TACUnaryNode(newchild2, TACOperator.INTTOREAL, child2))
            else:
                newchild2 = child2

            ret = Symbol(generator.gettemporary(), tok.location, pascaltypes.BooleanType())
            self.symboltable.add(ret)
            self.addnode(TACBinaryNode(ret, op, newchild1, newchild2))
            return ret
        else:
            raise TACException("TACBlock.processast - cannot process token:", str(tok))


class TACGenerator:
    def __init__(self, literaltable):
        assert isinstance(literaltable, LiteralTable)
        self.tacblocks = []
        self.nextlabel = 0
        self.nexttemporary = 0
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
            newblock = TACBlock(True)
        else:
            newblock = TACBlock(False)
            newblock.symboltable = deepcopy(ast.symboltable)
        newblock.symboltable.parent = self.globalsymboltable
        newblock.processast(ast, self)
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

    def printblocks(self):
        for block in self.tacblocks:
            if block.ismain:
                print("_MAIN:")
            block.printnodes()
