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
        IfZ {value} Goto {label} - if the value is zero, then goto the statement named by the label

    Functions / Procedures
        If a Procedure or Function takes parameters, then before the call to the function or procedure, one or more
        "param" calls will be made.  After the parameters are
        indicated, then a "Call" statement is executed with its parameter being the label corresponding to the
        function or procedure.  At the end of a procedure, the statement "return" occurs; if a function then
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
from symboltable import Symbol, Label, Literal, SymbolTable, LiteralTable
from lexer import TokenType
import pascaltypes


@unique
class TACOperator(Enum):
    LABEL = "label"
    ASSIGN = ":="
    ADD = "+"
    PARAM = "param"
    CALL = "call"

    def __str__(self):
        return self.value


class TACNode:
    def __init__(self, operator):
        assert isinstance(operator, TACOperator)
        self.operator = operator


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


class TACSystemFunctionNode(TACNode):
    def __init__(self, strlabel):
        super().__init__(TACOperator.CALL)
        self.strlabel = strlabel  # TODO this is ugly

    def __str__(self):
        return "{} {}".format(str(self.operator), self.strlabel)


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
        return "{} {} {}".format(str(self.lval), str(self.operator), str(self.literal1))


"""
class TACBinaryNode(TACNode):
    def __init__(self, result, operator, arg1, arg2):
        assert isinstance(result, Symbol)
        assert isinstance(arg1, Symbol)
        assert isinstance(arg2, Symbol)
        super().__init__(operator)
        self.result = result
        self.arg1 = arg1
        self.arg2 = arg2


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
    def __init__(self):
        self.tacnodes = []
        self.symboltable = SymbolTable()

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
        tok = ast.token
        if tok.tokentype == TokenType.WRITE:
            for child in ast.children:
                tmp = self.processast(child, generator)
                self.addnode(TACParamNode(tmp))
                self.addnode(TACSystemFunctionNode("_WRITEI"))
            return None
        elif tok.tokentype in [TokenType.UNSIGNED_INT, TokenType.SIGNED_INT]:
            ret = Symbol(generator.gettemporary(), tok.location, pascaltypes.IntegerType())
            self.symboltable.add(ret)
            self.addnode(TACUnaryLiteralNode(ret, TACOperator.ASSIGN, Literal(int(tok.value), tok.location,
                                                                              pascaltypes.IntegerType())))
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
            main = TACBlock()
            main.symboltable.parent = self.globalsymboltable
            main.addnode(TACLabelNode(Label("main")))
            for child in ast.children:
                main.processast(child, self)
            return main
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