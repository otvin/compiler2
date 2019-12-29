import os
from tac_ir import TACBlock, TACLabelNode, TACParamNode, TACCallSystemFunctionNode, TACUnaryLiteralNode, \
    TACOperator, TACGenerator, TACCommentNode, TACBinaryNode, TACUnaryNode, TACGotoNode, TACIFZNode, \
    TACFunctionReturnNode, TACCallFunctionNode
from symboltable import StringLiteral, NumericLiteral, Symbol, Parameter, ActivationSymbol, FunctionResultVariableSymbol
from editor_settings import NUM_SPACES_IN_TAB, NUM_TABS_FOR_COMMENT
import pascaltypes




class ASMGeneratorError(Exception):
    pass


# helper functions
VALID_REGISTER_LIST = ["RAX", "RBX", "RCX", "RDX", "RSI", "RDI", "RBP", "RSP", "R8", "R9", "R10", "R11", "R12",
                       "R13", "R14", "R15", "R16"]


def get_register_slice_bybytes(register, numbytes):
    assert numbytes in [1, 2, 4, 8]
    assert register in VALID_REGISTER_LIST

    # TODO - https://stackoverflow.com/questions/41573502/why-doesnt-gcc-use-partial-registers - when we get to types
    # that are 1 or 2 bytes, need to make sure we don't get in trouble.

    if numbytes == 8:
        ret = register
    else:
        if register in ["RAX", "RBX", "RCX", "RDX"]:
            if numbytes == 4:
                ret = "E" + register[-2:]
            elif numbytes == 2:
                ret = register[-2:]
            else:
                ret = register[1] + "L"
        elif register in ["RSI", "RDI", "RBP", "RSP"]:
            if numbytes == 4:
                ret = "E" + register[-2:]
            elif numbytes == 2:
                ret = register[-2:]
            else:
                ret = register[-2:] + "L"
        else:
            if numbytes == 4:
                ret = register + "D"
            elif numbytes == 2:
                ret = register + "W"
            else:
                ret = register + "B"
    return ret


def intparampos_to_register(pos):
    # First six integer parameters to functions are stored in registers.
    # This function converts the position in the function parameter list to a register
    # once we get > 6 parameters it will be stack pointer offsets
    assert pos in [1, 2, 3, 4, 5, 6]

    if pos == 1:
        ret = "RDI"
    elif pos == 2:
        ret = "RSI"
    elif pos == 3:
        ret = "RDX"
    elif pos == 4:
        ret = "RCX"
    elif pos == 5:
        ret = "R8"
    else:
        ret = "R9"

    return ret


class AssemblyGenerator:
    def __init__(self, asmfilename, tacgenerator):
        assert isinstance(tacgenerator, TACGenerator)
        self.asmfilename = asmfilename
        self.asmfile = open(asmfilename, 'w')
        self.tacgenerator = tacgenerator
        self.maxlabelnum = 0

    def emit(self, s):
        self.asmfile.write(s)

    def emitln(self, s):
        self.emit(s + '\n')

    def emitcode(self, s, comment=None):
        if comment is None:
            self.emitln('\t' + s)
        else:
            numtabs = NUM_TABS_FOR_COMMENT - 1 - (len(s) // NUM_SPACES_IN_TAB)
            if numtabs < 0:
                numtabs = 0
            tabstr = ""
            for i in range(numtabs):
                tabstr += "\t"
            self.emitln('\t' + s + tabstr + ';' + comment)

    def emitlabel(self, labelname, comment=None):
        if comment is None:
            self.emitln(labelname + ":")
        else:
            numtabs = NUM_TABS_FOR_COMMENT - (len(labelname) // NUM_SPACES_IN_TAB)
            if numtabs < 0:
                numtabs = 0
            tabstr = ""
            for i in range(numtabs):
                tabstr += "\t"
            self.emitln(labelname + ':' + tabstr + ';' + comment)

    def emitsection(self, sectionname):
        self.emitln("section .{}".format(sectionname))

    def emitcomment(self, commentstr, indented=False):

        tabstr = ""
        if indented:
            for i in range(NUM_TABS_FOR_COMMENT):
                tabstr += "\t"
        self.emitln("{}; {}".format(tabstr, commentstr))

    def emitpushxmmreg(self, reg):
        self.emitcode("SUB RSP, 16", "PUSH " + reg)
        self.emitcode("MOVDQU [RSP], " + reg)

    def emitpopxmmreg(self, reg):
        self.emitcode("MOVDQU " + reg + ", [RSP]", "POP " + reg)
        self.emitcode("ADD RSP, 16")

    def emit_movtoregister_fromstack(self, destreg, symbol, comment=None):
        # TODO - instead of hardcoded r10, have some way to get an available scratch register
        assert isinstance(symbol, Symbol)
        if symbol.is_byref:
            self.emitcode("mov r10, [{}]".format(symbol.memoryaddress), comment)
            self.emitcode("mov {}, [r10]".format(destreg))
        else:
            self.emitcode("mov {}, [{}]".format(destreg, symbol.memoryaddress), comment)

    def emit_movtoxmmregister_fromstack(self, destreg, symbol, comment=None):
        assert isinstance(symbol, Symbol)
        if symbol.is_byref:
            self.emitcode("mov r10, [{}]".format(symbol.memoryaddress), comment)
            self.emitcode("movsd {}, [r10]".format(destreg))
        else:
            self.emitcode("movsd {}, [{}]".format(destreg, symbol.memoryaddress), comment)

    def emit_movtostack_fromregister(self, symbol, sourcereg, comment=None):
        assert isinstance(symbol, Symbol)
        if symbol.is_byref:
            self.emitcode("mov r10, [{}]".format(symbol.memoryaddress), comment)
            self.emitcode("mov [r10], {}".format(sourcereg))
        else:
            self.emitcode("mov [{}], {}".format(symbol.memoryaddress, sourcereg), comment)

    def emit_movtostack_fromxmmregister(self, symbol, sourcereg, comment=None):
        assert isinstance(symbol, Symbol)
        if symbol.is_byref:
            self.emitcode("mov r10, [{}]".format(symbol.memoryaddress), comment)
            self.emitcode("movsd [r10], {}".format(sourcereg))
        else:
            self.emitcode("movsd [{}], {}".format(symbol.memoryaddress, sourcereg), comment)

    def getnextlabel(self):
        ret = "_L" + str(self.maxlabelnum)
        self.maxlabelnum += 1
        return ret

    def generate_externs(self):
        self.emitcode("extern printf")
        self.emitcode("extern fflush")

    def generate_datasection(self):
        self.emitsection("data")
        self.emitcomment("error handling strings")
        self.emitcode('_stringerr_0 db `Overflow error`, 0')
        self.emitcode('_stringerr_1 db `Division by zero error`, 0')
        self.emitcode('_stringerr_2 db `Error: Divisor in Mod must be positive`, 0')
        self.emitcode('_stringerr_3 db `Error: Cannot take sqrt() of negative number`, 0')
        self.emitcode('_stringerr_4 db `Error: Cannot take ln() of number less than or equal to zero`, 0')
        self.emitcomment("support for write() commands")
        self.emitcode('_printf_intfmt db "%d",0')
        self.emitcode('_printf_strfmt db "%s",0')
        # TODO - this is not pascal-compliant, as should be fixed characters right-justified
        # but is better than the C default of 6 digits to the right of the decimal.
        self.emitcode('_printf_realfmt db "%.12f",0')
        self.emitcode('_printf_newln db 10,0')
        self.emitcode('_printf_true db "TRUE",0')
        self.emitcode('_printf_false db "FALSE",0')
        if len(self.tacgenerator.globalliteraltable) > 0:
            nextid = 0
            for lit in self.tacgenerator.globalliteraltable:
                if isinstance(lit, StringLiteral):
                    litname = 'stringlit_{}'.format(nextid)
                    nextid += 1
                    if len(lit.value) > 255:
                        raise ASMGeneratorError("String literal {} exceeds 255 char max length.".format(lit.value))
                    self.emitcode("{} db `{}`, 0".format(litname, lit.value.replace('`', '\\`')))
                    lit.memoryaddress = litname
                elif isinstance(lit, NumericLiteral) and isinstance(lit.pascaltype, pascaltypes.RealType):
                    litname = 'reallit_{}'.format(nextid)
                    nextid += 1
                    self.emitcode("{} dq {}".format(litname, lit.value))
                    lit.memoryaddress = litname
                else:  # pragma: no cover
                    raise ASMGeneratorError("Invalid literal type")

    def generate_code(self):
        params = []  # this is a stack of parameters

        for block in self.tacgenerator.tacblocks:
            assert isinstance(block, TACBlock)

            if block.ismain:
                self.emitlabel("main")
                tacnodelist = block.tacnodes
            else:
                self.emitlabel(block.tacnodes[0].label.name, block.tacnodes[0].comment
                               )
                tacnodelist = block.tacnodes[1:]

            totalstorageneeded = 0  # measured in bytes

            for symname in block.symboltable.symbols.keys():
                sym = block.symboltable.fetch(symname)
                assert isinstance(sym, Symbol)
                if sym.memoryaddress is None:
                    # to ensure stack alignment, we subract 8 bytes from the stack even if we're putting in a 1, 2, or 4
                    # byte value.
                    totalstorageneeded += 8
                    sym.memoryaddress = "RBP-{}".format(str(totalstorageneeded))

            if totalstorageneeded > 0:
                self.emitcode("PUSH RBP")  # ABI requires callee to preserve RBP
                self.emitcode("MOV RBP, RSP", "save stack pointer")
                # X86-64 ABI requires stack to stay aligned to 16-byte boundary.  Make sure we subtract in chunks of 16
                # if we are in main.  If we are in a called function, we will begin with the stack 8-bytes off because
                # of the 8-byte return address pushed onto the stack.  However, the first thing we do is push RBP
                # which then gets us back to 16-byte alignment.
                # If we are ever out of alignment, we will segfault calling printf() with XMM registers

                if totalstorageneeded % 16 > 0:
                    totalstorageneeded += 16 - (totalstorageneeded % 16)
                self.emitcode("SUB RSP, " + str(totalstorageneeded), "allocate local storage")

                if not block.ismain:

                    numintparams = 0
                    numrealparams = 0

                    # this is just for getting the comments done
                    for param in block.paramlist:
                        localsym = block.symboltable.fetch(param.symbol.name)
                        self.emitcomment("Parameter {} - [{}]".format(param.symbol.name, localsym.memoryaddress), True)
                    for symname in block.symboltable.symbols.keys():
                        if block.paramlist.fetch(symname) is None:
                            localsym = block.symboltable.symbols[symname]
                            if isinstance(localsym, FunctionResultVariableSymbol):
                                self.emitcomment("Function Result - [{}]".format(localsym.memoryaddress), True)
                            else:
                                self.emitcomment("Local Variable {} - [{}]".format(symname,
                                                                                   localsym.memoryaddress), True)

                    for param in block.paramlist:
                        localsym = block.symboltable.fetch(param.symbol.name)
                        # TODO - this will break when we have so many parameters that they will get
                        # passed on the stack instead of in a register.
                        if param.is_byref:
                            numintparams += 1
                            paramreg = intparampos_to_register(numintparams)
                            self.emitcode("mov [{}], {}".format(localsym.memoryaddress, paramreg),
                                          "Copy variable parameter {} to stack".format(param.symbol.name))
                        elif isinstance(param.symbol.pascaltype, pascaltypes.RealType):
                            paramreg = "xmm{}".format(numrealparams)
                            numrealparams += 1
                            # the param memory address is one of the xmm registers.
                            self.emitcode("movq [{}], {}".format(localsym.memoryaddress, paramreg),
                                          "Copy parameter {} to stack".format(param.symbol.name))
                        else:
                            # the param memory address is a register
                            numintparams += 1
                            paramreg = intparampos_to_register(numintparams)
                            regslice = get_register_slice_bybytes(paramreg, param.symbol.pascaltype.size)
                            self.emitcode("mov [{}], {}".format(localsym.memoryaddress, regslice),
                                          "Copy parameter {} to stack".format(param.symbol.name))
                else:
                    for symname in block.symboltable.symbols.keys():
                        localsym = block.symboltable.symbols[symname]
                        if isinstance(localsym, FunctionResultVariableSymbol):
                            self.emitcomment("Function Result - [{}]".format(localsym.memoryaddress), True)
                        else:
                            self.emitcomment("Local Variable {} - [{}]".format(symname,
                                                                               localsym.memoryaddress), True)
            for node in tacnodelist:
                if isinstance(node, TACCommentNode):
                    self.emitcomment(node.comment)
                elif isinstance(node, TACLabelNode):
                    self.emitlabel(node.label.name, node.comment)
                elif isinstance(node, TACGotoNode):
                    self.emitcode("jmp {}".format(node.label.name))
                elif isinstance(node, TACIFZNode):
                    self.emitcode("mov al, [{}]".format(node.val.memoryaddress))
                    self.emitcode("test al,al")
                    self.emitcode("jz {}".format(node.label.name))
                elif isinstance(node, TACParamNode):
                    params.append(node)
                elif isinstance(node, TACFunctionReturnNode):
                    if isinstance(node.returnval, Symbol):
                        # do the function returning stuff here
                        # the "ret" itself is emitted below.
                        if isinstance(node.returnval.pascaltype, pascaltypes.IntegerType):
                            self.emitcode("mov EAX, [{}]".format(node.returnval.memoryaddress), "set up return value")
                        elif isinstance(node.returnval.pascaltype, pascaltypes.BooleanType):
                            # whereas mov EAX, [{}] will zero out the high 32 bits of RAX, moving AL will not.
                            self.emitcode("movzx RAX, BYTE [{}]".format(node.returnval.memoryaddress),
                                          "set up return value")
                        else:
                            self.emitcode("movsd XMM0, [{}]".format(node.returnval.memoryaddress), "set up return val")
                elif isinstance(node, TACUnaryNode):
                    if node.operator == TACOperator.INTTOREAL:
                        assert node.arg1.pascaltype.size in [1,2,4,8]
                        if node.arg1.pascaltype.size in (1, 2):
                            raise ASMGeneratorError("Cannot handle 8- or 16-bit int convert to real")
                        elif node.arg1.pascaltype.size == 4:
                            # extend to 8 bytes
                            self.emitcode("mov eax, [{}]".format(node.arg1.memoryaddress))
                            self.emitcode("cdqe")
                        else:
                            self.emitcode("mov rax, [{}]".format(node.arg1.memoryaddress))
                        # rax now has the value we need to convert to the float
                        comment = "convert {} to real, store result in {}".format(node.arg1.name, node.lval.name)
                        self.emitcode("cvtsi2sd xmm0, rax", comment)
                        # now save the float into its location
                        self.emitcode("movsd [{}], xmm0".format(node.lval.memoryaddress))
                    elif node.operator == TACOperator.ASSIGN:
                        reg = get_register_slice_bybytes("RAX", node.lval.pascaltype.size)

                        # first, get the arg1 into reg.  If arg1 is a byref parameter, we need to
                        # dereference the pointer.
                        comment = "Move {} into {}".format(node.arg1.name, node.lval.name)
                        self.emit_movtoregister_fromstack(reg, node.arg1, comment)

                        # now, get the value from reg into lval.  If lval is a byref parameter, we
                        # need to dereference the pointer.
                        self.emit_movtostack_fromregister(node.lval, reg)

                    else:  # pragma: no cover
                        raise ASMGeneratorError("Invalid operator: {}".format(node.operator))
                elif isinstance(node, TACUnaryLiteralNode):
                    if isinstance(node.literal1, StringLiteral):
                        # dealing with PEP8 line length
                        glt = self.tacgenerator.globalliteraltable
                        litaddress = glt.fetch(node.literal1.value, pascaltypes.StringLiteralType()).memoryaddress
                        comment = "Move literal '{}' into {}".format(node.literal1.value, node.lval.name)
                        self.emitcode("lea rax, [rel {}]".format(litaddress), comment)
                        self.emit_movtostack_fromregister(node.lval, "rax")
                    elif isinstance(node.literal1, NumericLiteral) and isinstance(node.literal1.pascaltype,
                                                                                  pascaltypes.RealType):
                        glt = self.tacgenerator.globalliteraltable
                        litaddress = glt.fetch(node.literal1.value, pascaltypes.RealType()).memoryaddress
                        comment = "Move literal {} into {}".format(node.literal1.value, node.lval.name)
                        self.emitcode("movsd xmm0, [rel {}]".format(litaddress), comment)
                        self.emit_movtostack_fromxmmregister(node.lval, "xmm0")
                    else:
                        # TODO is node.operator ever anything other than ASSIGN?
                        if node.operator == TACOperator.ASSIGN:
                            comment = "Move literal {} into {}".format(node.literal1.value, node.lval.name)
                            # putting the result into rax so I can use existing helper function vs.
                            # special casing this here.
                            tmpreg = get_register_slice_bybytes("RAX", node.lval.pascaltype.size)
                            self.emitcode("mov {}, {}".format(tmpreg, node.literal1.value), comment)
                            self.emit_movtostack_fromregister(node.lval, tmpreg)

                elif isinstance(node, TACCallFunctionNode) and \
                        not isinstance(node, TACCallSystemFunctionNode):
                    assert len(params) >= node.numparams
                    localparamlist = params[(-1 * node.numparams):]
                    numintparams = 0
                    numrealparams = 0
                    act_symbol = block.symboltable.parent.fetch(node.funcname)
                    assert isinstance(act_symbol, ActivationSymbol)
                    assert node.numparams == len(act_symbol.paramlist)  # mismatches are caught upstream

                    # localparamlist has a list of TACParamNodes - that has information of what is going in.
                    # act_symbol.paramlist has the information of where it goes
                    # remove this comment once code is done

                    for parampos in range(0, node.numparams):
                        # remember - pointers count as int parameters
                        actualparam = localparamlist[parampos]
                        paramdef = act_symbol.paramlist[parampos]
                        assert isinstance(actualparam, TACParamNode)
                        assert isinstance(paramdef, Parameter)

                        if paramdef.is_byref:
                            comment = "Parameter {} for {} ({}, ByRef)".format(paramdef.symbol.name,
                                                                               act_symbol.name,
                                                                               str(paramdef.symbol.pascaltype))
                        else:
                            comment = "Parameter {} for {} ({})".format(paramdef.symbol.name,
                                                                        act_symbol.name,
                                                                        str(paramdef.symbol.pascaltype))

                        if paramdef.is_byref and actualparam.paramval.is_byref:
                            # if the formal parameter is byref and actual parameter is byref, then just pass the
                            # value of the actual parameter on through, as that value is a memory address.
                            numintparams += 1
                            assert numintparams <= 6
                            reg = intparampos_to_register(numintparams)
                            self.emitcode("mov {}, [{}]".format(reg, actualparam.paramval.memoryaddress), comment)
                        elif paramdef.is_byref:
                            numintparams += 1
                            assert numintparams <= 6
                            reg = intparampos_to_register(numintparams)  # we use all 64 bytes for pointers
                            self.emitcode("LEA {}, [{}]".format(reg, actualparam.paramval.memoryaddress), comment)
                        elif isinstance(paramdef.symbol.pascaltype, pascaltypes.IntegerType) or \
                                isinstance(paramdef.symbol.pascaltype, pascaltypes.BooleanType):
                            numintparams += 1
                            assert numintparams <= 6  # TODO - remove when we can handle more
                            fullreg = intparampos_to_register(numintparams)
                            reg = get_register_slice_bybytes(fullreg, paramdef.symbol.pascaltype.size)
                            self.emit_movtoregister_fromstack(reg, actualparam.paramval, comment)
                        elif isinstance(paramdef.symbol.pascaltype, pascaltypes.RealType):
                            reg = "xmm{}".format(numrealparams)
                            numrealparams += 1
                            assert numrealparams <= 8
                            self.emit_movtoxmmregister_fromstack(reg, actualparam.paramval, comment)
                        else:
                            raise ASMGeneratorError("Invalid Parameter Type")
                    self.emitcode("call {}".format(node.label), "call {}()".format(node.funcname))
                    if act_symbol.returnpascaltype is not None:
                        # return value is now in either RAX or XMM0 - need to store it in right place
                        comment = "assign return value of function to {}".format(node.lval.name)
                        if isinstance(act_symbol.returnpascaltype, pascaltypes.IntegerType):
                            self.emitcode("MOV [{}], EAX".format(node.lval.memoryaddress), comment)
                        elif isinstance(act_symbol.returnpascaltype, pascaltypes.BooleanType):
                            self.emitcode("MOV [{}], AL".format(node.lval.memoryaddress), comment)
                        else:
                            self.emitcode("MOVSD [{}], XMM0".format(node.lval.memoryaddress), comment)
                    del params[(-1 * node.numparams):]
                elif isinstance(node, TACCallSystemFunctionNode):
                    if node.label.name == "_WRITEI":
                        if node.numparams != 1:  # pragma: no cover
                            raise ASMGeneratorError("Invalid numparams to _WRITEI")
                        self.emitcode("mov rdi, _printf_intfmt")
                        param = params[-1]
                        destregister = get_register_slice_bybytes("RSI", param.paramval.pascaltype.size)
                        self.emit_movtoregister_fromstack(destregister, param.paramval)
                        # must pass 0 (in rax) as number of floating point args since printf is variadic
                        self.emitcode("mov rax, 0")
                        self.emitcode("call printf wrt ..plt")
                        del params[-1]
                    elif node.label.name == "_WRITER":
                        if node.numparams != 1:  # pragma: no cover
                            raise ASMGeneratorError("Invalid numparams to _WRITER")
                        self.emitcode("mov rdi, _printf_realfmt")
                        self.emit_movtoxmmregister_fromstack("xmm0", params[-1].paramval)
                        self.emitcode("mov rax, 1", "1 floating point param")
                        self.emitcode("call printf wrt ..plt")
                        del params[-1]
                    elif node.label.name == "_WRITES":
                        self.emitcode("mov rdi, _printf_strfmt")
                        self.emit_movtoregister_fromstack("RSI", params[-1].paramval)
                        self.emitcode("mov rax, 0")
                        self.emitcode("call printf wrt ..plt")
                        del params[-1]
                    elif node.label.name == "_WRITEB":
                        self.emitcode("mov rdi, _printf_strfmt")
                        self.emit_movtoregister_fromstack("al", params[-1].paramval)
                        self.emitcode("test al, al")
                        labelfalse = self.getnextlabel()
                        labelprint = self.getnextlabel()
                        self.emitcode("je {}".format(labelfalse))
                        self.emitcode("mov rsi, _printf_true")
                        self.emitcode("jmp {}".format(labelprint))
                        self.emitlabel(labelfalse)
                        self.emitcode("mov rsi, _printf_false")
                        self.emitlabel(labelprint)
                        self.emitcode("mov rax, 0")
                        self.emitcode("call printf wrt ..plt")
                        del params[-1]
                    elif node.label.name == "_WRITECRLF":
                        self.emitcode("mov rdi, _printf_newln")
                        self.emitcode("mov rax, 0")
                        self.emitcode("call printf wrt ..plt")
                        self.emitcode("XOR RDI, RDI", "Flush standard output when we do a writeln")
                        self.emitcode("CALL fflush wrt ..plt")
                        self.emitcode("")
                    elif node.label.name == "_SQRTR":
                        comment = "parameter {} for sqrt()".format(str(params[-1].paramval))
                        self.emit_movtoxmmregister_fromstack("xmm0", params[-1].paramval, comment)
                        self.emitcode("xorps xmm8, xmm8", "validate parameter is >= 0")
                        self.emitcode("ucomisd xmm0, xmm8")
                        self.emitcode("jb _PASCAL_SQRT_ERROR")
                        self.emitcode("sqrtsd xmm0, xmm0", 'sqrt()')
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emitcode("MOVSD [{}], XMM0".format(node.lval.memoryaddress), comment)
                    else:  # pragma: no cover
                        raise ASMGeneratorError("Invalid System Function: {}".format(node.label.name))
                elif isinstance(node, TACBinaryNode):
                    comment = "{} := {} {} {}".format(node.result.name, node.arg1.name, node.operator, node.arg2.name)

                    if isinstance(node.result.pascaltype, pascaltypes.IntegerType):
                        # TODO - handle something other than 4-byte integers
                        if node.operator in (TACOperator.MULTIPLY, TACOperator.ADD, TACOperator.SUBTRACT):
                            if node.operator == TACOperator.MULTIPLY:
                                op = "imul"
                            elif node.operator == TACOperator.ADD:
                                op = "add"
                            else:
                                op = "sub"

                            self.emit_movtoregister_fromstack("eax", node.arg1, comment)
                            self.emit_movtoregister_fromstack("r11d", node.arg2)
                            self.emitcode("{} eax, r11d".format(op))
                            self.emitcode("jo _PASCAL_OVERFLOW_ERROR")
                            self.emit_movtostack_fromregister(node.result, "eax")

                        elif node.operator in (TACOperator.IDIV, TACOperator.MOD):
                            self.emit_movtoregister_fromstack("eax", node.arg1, comment)
                            self.emit_movtoregister_fromstack("r11d", node.arg2)

                            # Error D.45: 6.7.2.2 of ISO Standard requires testing for division by zero at runtime
                            # Error D.46: 6.7.2.2 also says it is an error if the divisor is not positive
                            # 6.7.2.2 also says that the result of the mod operation must be greater than or
                            # equal to zero, and less than the divisor.
                            self.emitcode("test r11d, r11d", "check for division by zero")
                            if node.operator == TACOperator.IDIV:
                                self.emitcode("je _PASCAL_DIVZERO_ERROR")
                            else:
                                self.emitcode("jle _PASCAL_MOD_ERROR")
                            self.emitcode("cdq", "sign extend eax -> edx:eax")
                            self.emitcode("idiv r11d")
                            if node.operator == TACOperator.MOD:
                                self.emitcode("MOV EAX, EDX", "Remainder of IDIV is in EDX")
                                posmodlabel = self.getnextlabel()
                                self.emitcode("CMP EAX, 0")
                                self.emitcode("JGE {}".format(posmodlabel))
                                self.emitcode("IMUL EAX, -1")
                                self.emitlabel(posmodlabel)
                            self.emit_movtostack_fromregister(node.result, "eax")
                        else:  # pragma: no cover
                            raise ASMGeneratorError("Unrecognized operator: {}".format(node.operator))
                    elif isinstance(node.result.pascaltype, pascaltypes.RealType):
                        if node.operator == TACOperator.MULTIPLY:
                            op = "mulsd"
                        elif node.operator == TACOperator.ADD:
                            op = "addsd"
                        elif node.operator == TACOperator.SUBTRACT:
                            op = "subsd"
                        elif node.operator == TACOperator.DIVIDE:
                            op = "divsd"
                        else:  # pragma: no cover
                            raise ASMGeneratorError("Unrecognized operator: {}".format(node.operator))
                        self.emit_movtoxmmregister_fromstack("xmm0", node.arg1, comment)
                        self.emit_movtoxmmregister_fromstack("xmm8", node.arg2, comment)
                        self.emitcode("{} xmm0, xmm8".format(op))
                        self.emit_movtostack_fromxmmregister(node.result, "xmm0")

                    elif isinstance(node.result.pascaltype, pascaltypes.BooleanType):
                        n1type = node.arg1.pascaltype
                        n2type = node.arg2.pascaltype
                        if type(n1type) != type(n2type):  # pragma: no cover
                            raise ASMGeneratorError("Cannot mix {} and {} with relational operator".format(str(n1type),
                                                                                                           str(n2type)))
                        if isinstance(n1type, pascaltypes.BooleanType) or isinstance(n1type, pascaltypes.IntegerType):
                            # Boolean and Integer share same jump instructions
                            if node.operator == TACOperator.EQUALS:
                                jumpinstr = "JE"
                            elif node.operator == TACOperator.NOTEQUAL:
                                jumpinstr = "JNE"
                            elif node.operator == TACOperator.GREATER:
                                jumpinstr = "JG"
                            elif node.operator == TACOperator.GREATEREQ:
                                jumpinstr = "JGE"
                            elif node.operator == TACOperator.LESS:
                                jumpinstr = "JL"
                            elif node.operator == TACOperator.LESSEQ:
                                jumpinstr = "JLE"
                            else:  # pragma: no cover
                                raise ASMGeneratorError("Invalid Relational Operator {}".format(node.operator))
                        elif isinstance(n1type, pascaltypes.RealType):
                            if node.operator == TACOperator.EQUALS:
                                jumpinstr = "JE"
                            elif node.operator == TACOperator.NOTEQUAL:
                                jumpinstr = "JNE"
                            elif node.operator == TACOperator.GREATER:
                                jumpinstr = "JA"
                            elif node.operator == TACOperator.GREATEREQ:
                                jumpinstr = "JAE"
                            elif node.operator == TACOperator.LESS:
                                jumpinstr = "JB"
                            elif node.operator == TACOperator.LESSEQ:
                                jumpinstr = "JBE"
                            else:  # pragma: no cover
                                raise ASMGeneratorError("Invalid Relational Operator {}".format(node.operator))
                        else:  # pragma: no cover
                            raise ASMGeneratorError("Invalid Type {}".format(str(n1type)))

                        if isinstance(n1type, pascaltypes.BooleanType):
                            self.emit_movtoregister_fromstack("al", node.arg1, comment)
                            self.emit_movtoregister_fromstack("r11b", node.arg2)
                            self.emitcode("cmp al, r11b")
                        elif isinstance(n1type, pascaltypes.IntegerType):
                            self.emit_movtoregister_fromstack("eax", node.arg1, comment)
                            self.emit_movtoregister_fromstack("r11d", node.arg2)
                            self.emitcode("cmp eax, r11d")
                        else:  # has to be real; we errored above if any other type
                            self.emit_movtoxmmregister_fromstack("xmm0", node.arg1)
                            self.emit_movtoxmmregister_fromstack("xmm8", node.arg2)
                            self.emitcode("ucomisd xmm0, xmm8")

                        labeltrue = self.getnextlabel()
                        labeldone = self.getnextlabel()
                        self.emitcode("{} {}".format(jumpinstr, labeltrue))
                        self.emitcode("mov al, 0")
                        self.emitcode("jmp {}".format(labeldone))
                        self.emitlabel(labeltrue)
                        self.emitcode("mov al, 1")
                        self.emitlabel(labeldone)
                        self.emit_movtostack_fromregister(node.result, "al")
                    else:  # pragma: no cover
                        raise ASMGeneratorError("Invalid Type {}".format(str(node.result.pascaltype)))
                else:  # pragma: no cover
                    raise ASMGeneratorError("Unknown TAC node type: {}".format(type(node)))

            if totalstorageneeded > 0:
                self.emitcode("MOV RSP, RBP", "restore stack pointer")
                self.emitcode("POP RBP")
            if not block.ismain:
                self.emitcode("RET")

    def generate_errorhandlingcode(self):
        # overflow
        self.emitcomment("overflow error")
        self.emitlabel("_PASCAL_OVERFLOW_ERROR")
        self.emitcode("mov rdi, _stringerr_0")
        self.emitcode("jmp _PASCAL_PRINT_ERROR")
        self.emitlabel("_PASCAL_DIVZERO_ERROR")
        self.emitcode("mov rdi, _stringerr_1")
        self.emitcode("jmp _PASCAL_PRINT_ERROR")
        self.emitlabel("_PASCAL_MOD_ERROR")
        self.emitcode("mov rdi, _stringerr_2")
        self.emitcode("jmp _PASCAL_PRINT_ERROR")
        self.emitlabel("_PASCAL_SQRT_ERROR")
        self.emitcode("mov rdi, _stringerr_3")
        self.emitcode("jmp _PASCAL_PRINT_ERROR")
        self.emitlabel("_PASCAL_LN_ERROR")
        self.emitcode("mov rdi, _stringerr_4")
        self.emitcode("jmp _PASCAL_PRINT_ERROR")

        self.emitlabel("_PASCAL_PRINT_ERROR")
        self.emitcomment("required: pointer to error message in rdi")
        self.emitcode("mov rax, 0")
        self.emitcode("call printf wrt ..plt")
        self.emitcode("jmp _PASCAL_EXIT")
        self.emitcomment("exit program")
        self.emitlabel("_PASCAL_EXIT")
        self.emitcomment("Need to flush the stdout buffer, as exiting does not do it.")
        self.emitcode("XOR RDI, RDI")
        self.emitcode("CALL fflush wrt ..plt")
        self.emitcode("MOV EAX, 60")
        self.emitcode("SYSCALL")

    def generate_textsection(self):
        self.emitsection("text")
        self.emitcode("global main")
        self.generate_code()
        self.emitcode("JMP _PASCAL_EXIT")
        self.generate_errorhandlingcode()

    def generate_bsssection(self):
        if len(self.tacgenerator.globalsymboltable.symbols.keys()) > 0:
            self.emitsection("bss")
            varseq = 0
            for symname in self.tacgenerator.globalsymboltable.symbols.keys():
                sym = self.tacgenerator.globalsymboltable.fetch(symname)
                assert isinstance(sym, Symbol)
                if not isinstance(sym, ActivationSymbol):
                    label = "_globalvar_{}".format(str(varseq))
                    varseq += 1
                    sym.memoryaddress = "rel {}".format(label)
                    self.emitcode("{} resb {}".format(label, sym.pascaltype.size), "global variable {}".format(symname))

    def generate(self, objfilename, exefilename):
        self.generate_externs()
        self.generate_bsssection()
        self.generate_datasection()
        self.generate_textsection()
        self.asmfile.close()
        os.system("nasm -f elf64 -F dwarf -g -o {} {}".format(objfilename, self.asmfilename))
        os.system("gcc {} -o {}".format(objfilename, exefilename))
