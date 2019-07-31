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
from parser import AST
from symboltable import Symbol, Label, Literal, NumericLiteral, StringLiteral, SymbolTable, LiteralTable
from lexer import TokenType
import pascaltypes


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
    PARAM = "param"
    CALL = "call"
    COMMENT = "comment"
    INTTOREAL = "is int_to_real"

    def __str__(self):
        return self.value


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
    def __init__(self, label):
        assert isinstance(label, Label)
        super().__init__(TACOperator.LABEL)
        self.label = label

    def __str__(self):
        return "{}:".format(self.label)


class TACParamNode(TACNode):
    def __init__(self, paramval):
        assert isinstance(paramval, Symbol)
        super().__init__(TACOperator.PARAM)
        self.paramval = paramval

    def __str__(self):
        return "{} {}".format(str(self.operator), str(self.paramval))


class TACCallFunctionNode(TACNode):
    def __init__(self, label, numparams):
        assert isinstance(label, Label)
        assert isinstance(numparams, int)
        assert numparams >= 0
        super().__init__(TACOperator.CALL)
        self.label = label
        self.numparams = numparams

    def __str__(self):
        return "{} {} {}".format(str(self.operator), self.label, str(self.numparams))


class TACCallSystemFunctionNode(TACCallFunctionNode):
    def __init__(self, label, numparams):
        super().__init__(label, numparams)


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
        if isinstance(self.literal1, NumericLiteral):
            litval = str(self.literal1)
        elif isinstance(self.literal1, StringLiteral):
            litval = '"{}"'.format(str(self.literal1).replace('"', '\"'))
        return "{} {} {}".format(str(self.lval), str(self.operator), litval)


# TODO if there is something other than T0 := T1 <oper> T2 then need to take the first operator
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
    """
    def __init__(self, label):
        assert isinstance(label, Label)
        self.label = label
        self.tacnodes = []
        self.symboltable = SymbolTable()
        # TODO - we need to add some representation of the expected parameters

    def addnode(self, node):
        assert isinstance(node, TACNode)
        self.tacnodes.append(node)

    def printnodes(self):
        for node in self.tacnodes:
            print(str(node))

    # TODO - fix passing the generator around like this it's ugly
    def processast(self, ast, generator):
        """ returns the Symbol of a temporary that holds the result of this computation """
        assert isinstance(ast, AST)
        assert isinstance(generator, TACGenerator)
        if ast.comment != "":
            self.addnode(TACCommentNode(ast.comment))
        tok = ast.token
        if tok.tokentype in (TokenType.WRITE, TokenType.WRITELN):
            for child in ast.children:
                tmp = self.processast(child, generator)
                self.addnode(TACParamNode(tmp))
                if isinstance(tmp.pascaltype, pascaltypes.StringLiteralType):
                    self.addnode(TACCallSystemFunctionNode(Label("_WRITES"), 1))
                elif isinstance(tmp.pascaltype, pascaltypes.RealType):
                    self.addnode(TACCallSystemFunctionNode(Label("_WRITER"), 1))
                else:
                    self.addnode(TACCallSystemFunctionNode(Label("_WRITEI"), 1))
            if tok.tokentype == TokenType.WRITELN:
                self.addnode(TACCallSystemFunctionNode(Label("_WRITECRLF"), 0))
            return None
        elif tok.tokentype in [TokenType.UNSIGNED_INT, TokenType.SIGNED_INT]:
            ret = Symbol(generator.gettemporary(), tok.location, pascaltypes.IntegerType())
            self.symboltable.add(ret)
            self.addnode(TACUnaryLiteralNode(ret, TACOperator.ASSIGN,
                                             NumericLiteral(int(tok.value), tok.location, pascaltypes.IntegerType())))
            return ret
        elif tok.tokentype in [TokenType.UNSIGNED_REAL, TokenType.SIGNED_REAL]:
            ret = Symbol(generator.gettemporary(), tok.location, pascaltypes.RealType())
            self.symboltable.add(ret)
            self.addnode(TACUnaryLiteralNode(ret, TACOperator.ASSIGN,
                                             NumericLiteral(float(tok.value), tok.location, pascaltypes.RealType())))
            return ret
        elif tok.tokentype == TokenType.CHARSTRING:
            ret = Symbol(generator.gettemporary(), tok.location, pascaltypes.StringLiteralType())
            self.symboltable.add(ret)
            self.addnode(TACUnaryLiteralNode(ret, TACOperator.ASSIGN, StringLiteral(tok.value, tok.location)))
            return ret
        elif tok.tokentype in (TokenType.MULTIPLY, TokenType.PLUS, TokenType.MINUS, TokenType.DIVIDE):
            if tok.tokentype == TokenType.MULTIPLY:
                op = TACOperator.MULTIPLY
            elif tok.tokentype == TokenType.PLUS:
                op = TACOperator.ADD
            elif tok.tokentype == TokenType.MINUS:
                op = TACOperator.SUBTRACT
            elif tok.tokentype == TokenType.DIVIDE:
                op = TACOperator.DIVIDE
            else:
                raise Exception("Do I need an exception here?")

            child1 = self.processast(ast.children[0], generator)
            child2 = self.processast(ast.children[1], generator)
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
            if tok.tokentype == TokenType.IDIV:
                op = TACOperator.IDIV
            else:
                op = TACOperator.MOD
            child1 = self.processast(ast.children[0], generator)
            child2 = self.processast(ast.children[1], generator)
            if isinstance(child1.pascaltype, pascaltypes.RealType) or\
                    isinstance(child2.pascaltype, pascaltypes.RealType):
                raise ValueError("Cannot use integer division with Real values.")
            ret = Symbol(generator.gettemporary(), tok.location, pascaltypes.IntegerType())
            self.symboltable.add(ret)
            self.addnode(TACBinaryNode(ret, op, child1, child2))
            return ret
        else:
            raise ValueError("Oops!")


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
        # process the main begin
        if ast.token.tokentype == TokenType.BEGIN:
            main = TACBlock(Label("main"))
            main.symboltable.parent = self.globalsymboltable
            for child in ast.children:
                main.processast(child, self)
            return main
        # when we get to if the token type is function or procedure call, then what I think
        # we need to do is something like:
        # paramlist = []
        # for each child in ast.children:
        #   paramlist.add(tacblock.processast(child, self)
        # for each symbol in paramlist
        #   tacblock.addnode(a node with TACOpearator.PARAM and symbol)
        # tacblock.addnode(a node with TACOperator.CALL, the label for the proc/func, and the len of paramlist)
        else:
            raise ValueError("Oops!")

    def generate(self, ast):
        assert isinstance(ast, AST)
        if ast.token.tokentype == TokenType.PROGRAM:
            for child in ast.children:
                self.addblock(self.generateblock(child))
        else:
            raise ValueError("Oops!")

    def getlabel(self):
        label = "L_" + str(self.nextlabel)
        self.nextlabel += 1
        return label

    def gettemporary(self):
        temporary = "T_" + str(self.nexttemporary)
        self.nexttemporary += 1
        return temporary

    def printblocks(self):
        for block in self.tacblocks:
            block.printnodes()
