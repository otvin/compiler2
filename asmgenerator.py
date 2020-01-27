import os
from tac_ir import TACBlock, TACLabelNode, TACParamNode, TACCallSystemFunctionNode, TACUnaryLiteralNode, \
    TACOperator, TACGenerator, TACCommentNode, TACBinaryNode, TACUnaryNode, TACGotoNode, TACIFZNode, \
    TACFunctionReturnNode, TACCallFunctionNode, TACBinaryNodeWithBoundsCheck
from symboltable import StringLiteral, IntegerLiteral, Symbol, Parameter, ActivationSymbol, RealLiteral, \
    FunctionResultVariableSymbol, CharacterLiteral
from editor_settings import NUM_SPACES_IN_TAB, NUM_TABS_FOR_COMMENT
import pascaltypes


class ASMGeneratorError(Exception):
    pass


# helper functions
VALID_REGISTER_LIST = ["RAX", "RBX", "RCX", "RDX", "RSI", "RDI", "RBP", "RSP", "R8", "R9", "R10", "R11", "R12",
                       "R13", "R14", "R15", "R16"]

VALID_DWORD_REGISTER_LIST = ["EAX", "EBX", "ECX", "EDX", "ESI", "EDI", "EBP", "ESP", "R8D", "R9D", "R10D", "R11D",
                             "R12D", "R13D", "R14D", "R15D", "R16D"]


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


def is_integerorboolean_subrangetype(basetype):
    assert isinstance(basetype, pascaltypes.BaseType)
    ret = False
    if isinstance(basetype, pascaltypes.SubrangeType):
        if isinstance(basetype.hosttypedef.basetype, pascaltypes.IntegerType):
            ret = True
        elif isinstance(basetype.hosttypedef.basetype, pascaltypes.BooleanType):
            ret = True
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
            tabstr = "\t" * numtabs
            self.emitln('\t' + s + tabstr + ';' + comment)

    def emitlabel(self, labelname, comment=None):
        if comment is None:
            self.emitln(labelname + ":")
        else:
            numtabs = NUM_TABS_FOR_COMMENT - (len(labelname) // NUM_SPACES_IN_TAB)
            if numtabs < 0:
                numtabs = 0
            tabstr = "\t" * numtabs
            self.emitln(labelname + ':' + tabstr + ';' + comment)

    def emitsection(self, sectionname):
        self.emitln("section .{}".format(sectionname))

    def emitcomment(self, commentstr, indented=False):
        tabstr = ""
        if indented:
            tabstr = "\t" * NUM_TABS_FOR_COMMENT
        self.emitln("{}; {}".format(tabstr, commentstr))

    def emitpushxmmreg(self, reg):
        self.emitcode("SUB RSP, 16", "PUSH " + reg)
        self.emitcode("MOVDQU [RSP], " + reg)

    def emitpopxmmreg(self, reg):
        self.emitcode("MOVDQU " + reg + ", [RSP]", "POP " + reg)
        self.emitcode("ADD RSP, 16")

    def emit_movtoregister_fromstack(self, destreg, symbol, comment=None):
        assert isinstance(symbol, Symbol)

        # function exists because it was written before we fixed literals.  The only difference is the assertion that
        # we are moving a symbol not a literal, and this is done so that if literals pop up someplace unexpected
        # we get a notice
        self.emit_movtoregister_fromstackorliteral(destreg, symbol, comment)

    def emit_movtoregister_fromstackorliteral(self, destreg, symbol, comment=None):
        # TODO - instead of hardcoded r10, have some way to get an available scratch register
        assert isinstance(symbol, Symbol) or isinstance(symbol, IntegerLiteral)

        if destreg.upper() in VALID_DWORD_REGISTER_LIST and symbol.typedef.basetype.size == 1:
            # we can find ourselves doing pointer math where we need to multiply the value from an enumerated
            # type by an integer representing the component size of an array.  Need to zero-extend that.  It
            # may come up in other cases as well.
            movinstr = "movzx"
            bytekeyword = " byte "
        else:
            movinstr = "mov"
            bytekeyword = ""

        if isinstance(symbol, IntegerLiteral):
            self.emitcode("mov {}, {}".format(destreg, symbol.value), comment)
        else:
            if symbol.is_byref:
                self.emitcode("mov r10, [{}]".format(symbol.memoryaddress), comment)
                self.emitcode("{} {}, {} [r10]".format(movinstr, destreg, bytekeyword))
            else:
                self.emitcode("{} {}, {} [{}]".format(movinstr, destreg, bytekeyword, symbol.memoryaddress), comment)

    def emit_movtoxmmregister_fromstack(self, destreg, symbol, comment=None):
        assert isinstance(symbol, Symbol)
        if symbol.is_byref:
            self.emitcode("mov r10, [{}]".format(symbol.memoryaddress), comment)
            self.emitcode("movsd {}, [r10]".format(destreg))
        else:
            self.emitcode("movsd {}, [{}]".format(destreg, symbol.memoryaddress), comment)

    def emit_movaddresstoregister_fromstack(self, destreg, symbol, comment=None):
        assert isinstance(symbol, Symbol)
        if symbol.is_byref or isinstance(symbol.typedef, pascaltypes.ArrayTypeDef):
            self.emitcode("mov {}, [{}]".format(destreg, symbol.memoryaddress), comment)
        else:
            self.emitcode("lea {}, [{}]".format(destreg, symbol.memoryaddress), comment)

    def emit_movdereftoregister_fromstack(self, destreg, symbol, comment=None):
        assert isinstance(symbol, Symbol)
        assert not symbol.is_byref  # not 100% positive this will be true
        self.emitcode("mov r10, [{}]".format(symbol.memoryaddress), comment)
        self.emitcode("mov {}, [r10]".format(destreg))

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

    def emit_memcopy(self, destsym, sourcesym, numbytes, comment="", preserve_regs=False):
        # the memcopy uses rdi, rsi, and rcx.  If preserve_regs is true, we will push/pop them to ensure
        # they are in same state as they were on entry

        # this is a bit hacky - sometimes I have a destination symbol, sometimes a register.  Since Python is
        # not statically typed, I can have one function handle either type of input, but it may not be very clean.

        assert isinstance(sourcesym, Symbol)
        assert isinstance(destsym, Symbol) or (isinstance(destsym, str) and destsym.upper() in VALID_REGISTER_LIST)
        assert numbytes > 0
        assert isinstance(sourcesym.typedef, pascaltypes.PointerTypeDef) or \
            isinstance(sourcesym.typedef, pascaltypes.ArrayTypeDef)
        if isinstance(destsym, Symbol):
            assert isinstance(destsym.typedef, pascaltypes.PointerTypeDef) or \
                   isinstance(destsym.typedef, pascaltypes.ArrayTypeDef)

        if preserve_regs:
            self.emitcode("push rcx", "preserve registers used in memcopy")
            self.emitcode("push rsi")
            self.emitcode("push rdi")

        if isinstance(destsym, Symbol):
            self.emitcode("mov rdi, [{}]".format(destsym.memoryaddress, comment))
        else:
            self.emitcode("mov rdi, {}".format(destsym))
        self.emitcode("mov rsi, [{}]".format(sourcesym.memoryaddress))
        self.emitcode("mov rcx, {}".format(numbytes))
        self.emitcode("cld")
        self.emitcode("rep movsb")

        if preserve_regs:
            self.emitcode("pop rdi")
            self.emitcode("pop rsi")
            self.emitcode("pop rcx")

    def getnextlabel(self):
        ret = "_L" + str(self.maxlabelnum)
        self.maxlabelnum += 1
        return ret

    def generate_externs(self):
        self.emitcode("extern printf")
        self.emitcode("extern putchar")
        self.emitcode("extern calloc")
        self.emitcode("extern free")
        self.emitcode("extern fflush")

    def generate_datasection(self):
        self.emitsection("data")
        self.emitcomment("error handling strings")
        # TODO - Rename the string values to include the official pascal error codes
        self.emitcode('_stringerr_0 db `Overflow error`, 0')
        self.emitcode('_stringerr_1 db `Division by zero error`, 0')
        self.emitcode('_stringerr_2 db `Error: Divisor in Mod must be positive`, 0')
        self.emitcode('_stringerr_3 db `Error: Cannot take sqrt() of negative number`, 0')
        self.emitcode('_stringerr_4 db `Error: Cannot take ln() of number less than or equal to zero`, 0')
        self.emitcode('_stringerr_5 db `Error: value to chr() exceeds 0-255 range for Char type`, 0')
        self.emitcode('_stringerr_6 db `Error: succ() or pred() exceeds range for enumerated type`, 0')
        self.emitcode('_stringerr_7 db `Error: value exceeds range for subrange type`, 0')
        self.emitcode('_stringerr_8 db `Error: array index out of range.`, 0')
        self.emitcode('_stringerr_9 db `Error: dynamic memory allocation failed.`, 0')
        self.emitcode('_stringerr_10 db `Error: unable to de-allocate dynamic memory.`, 0')
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
                if isinstance(lit, IntegerLiteral) or isinstance(lit, CharacterLiteral):
                    # these can be defined as part of the instruction where they are loaded
                    pass
                elif isinstance(lit, StringLiteral):
                    litname = 'stringlit_{}'.format(nextid)
                    nextid += 1
                    if len(lit.value) > 255:
                        raise ASMGeneratorError("String literal {} exceeds 255 char max length.".format(lit.value))
                    self.emitcode("{} db `{}`, 0".format(litname, lit.value.replace('`', '\\`')))
                    lit.memoryaddress = litname
                elif isinstance(lit, RealLiteral):
                    litname = 'reallit_{}'.format(nextid)
                    nextid += 1
                    self.emitcode("{} dq {}".format(litname, lit.value))
                    lit.memoryaddress = litname
                else:  # pragma: no cover
                    raise ASMGeneratorError("Invalid literal type")

    def generate_subrangetest_code(self, reg, subrange_basetype):
        assert isinstance(subrange_basetype, pascaltypes.SubrangeType)
        comment = "Validate we are within proper range"
        self.emitcode("CMP {}, {}".format(reg, subrange_basetype.rangemin_int), comment)
        self.emitcode("JL _PASCAL_SUBRANGE_ERROR")
        self.emitcode("CMP {}, {}".format(reg, subrange_basetype.rangemax_int))
        self.emitcode("JG _PASCAL_SUBRANGE_ERROR")

    def generate_code(self):
        params = []  # this is a stack of parameters

        for block in self.tacgenerator.tacblocks:
            assert isinstance(block, TACBlock)

            if block.ismain:
                self.emitlabel("main")
                self.emitcode("finit")  # TODO - this should only be written if we use x87 anywhere.

                # need to init any global variables that are arrays
                for symname in self.tacgenerator.globalsymboltable.symbols.keys():
                    sym = self.tacgenerator.globalsymboltable.fetch(symname)
                    if isinstance(sym, Symbol) and isinstance(sym.typedef, pascaltypes.ArrayTypeDef):
                        self.emitcode("mov rdi, {}".format(sym.typedef.basetype.numitemsinarray),
                                      'Allocate memory for global array {}'.format(symname))
                        self.emitcode("mov rsi, {}".format(sym.typedef.basetype.componenttypedef.basetype.size))
                        self.emitcode("call _PASCAL_ALLOCATE_MEMORY")
                        self.emitcode("mov [{}], rax".format(sym.memoryaddress))
                tacnodelist = block.tacnodes
            else:
                self.emitlabel(block.tacnodes[0].label.name, block.tacnodes[0].comment)
                tacnodelist = block.tacnodes[1:]

            totalstorageneeded = 0  # measured in bytes

            for symname in block.symboltable.symbols.keys():
                sym = block.symboltable.fetch(symname)
                if isinstance(sym, Symbol):
                    if sym.memoryaddress is None:
                        # to ensure stack alignment, we subract 8 bytes from the stack even if we're putting in
                        # a 1, 2, or 4 byte value.
                        totalstorageneeded += 8
                        sym.memoryaddress = "RBP-{}".format(str(totalstorageneeded))

            if totalstorageneeded > 0 or block.ismain:
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

                    # this is just to put the comments above all the code, making the asm more readable.
                    for param in block.paramlist:
                        localsym = block.symboltable.fetch(param.symbol.name)
                        self.emitcomment("Parameter {} - [{}]".format(param.symbol.name, localsym.memoryaddress), True)
                    for symname in block.symboltable.symbols.keys():
                        if block.paramlist.fetch(symname) is None:
                            localsym = block.symboltable.symbols[symname]
                            if isinstance(localsym, Symbol):
                                if isinstance(localsym, FunctionResultVariableSymbol):
                                    self.emitcomment("Function Result - [{}]".format(localsym.memoryaddress), True)
                                else:
                                    self.emitcomment("Local Variable {} - [{}]".format(symname,
                                                                                       localsym.memoryaddress), True)

                    for param in block.paramlist:
                        localsym = block.symboltable.fetch(param.symbol.name)
                        # TODO - this will break when we have so many parameters that they will get
                        # passed on the stack instead of in a register.
                        if isinstance(param.symbol.typedef, pascaltypes.ArrayTypeDef):
                            # array parameters are always the address of the array.  If it is byref, the caller
                            # will pass in the address of the original array.  If it is byval, the caller will copy
                            # the array and provide the address of the copy.  In either case, we just move the
                            # parameter to the stack as-is.
                            numintparams += 1
                            paramreg = intparampos_to_register(numintparams)
                            if param.is_byref:
                                comment = "Copy address of variable array parameter {} to stack"
                            else:
                                comment = "Copy address of array parameter {} to stack"
                            comment = comment.format(param.symbol.name)
                            self.emitcode("mov [{}], {}".format(localsym.memoryaddress, paramreg, comment))
                        elif param.is_byref:
                            numintparams += 1
                            paramreg = intparampos_to_register(numintparams)
                            self.emitcode("mov [{}], {}".format(localsym.memoryaddress, paramreg),
                                          "Copy variable parameter {} to stack".format(param.symbol.name))
                        elif isinstance(param.symbol.typedef.basetype, pascaltypes.RealType):
                            paramreg = "xmm{}".format(numrealparams)
                            numrealparams += 1
                            # the param memory address is one of the xmm registers.
                            self.emitcode("movq [{}], {}".format(localsym.memoryaddress, paramreg),
                                          "Copy parameter {} to stack".format(param.symbol.name))
                        else:
                            # the param memory address is a register
                            numintparams += 1
                            paramreg = intparampos_to_register(numintparams)
                            regslice = get_register_slice_bybytes(paramreg, param.symbol.typedef.basetype.size)
                            self.emitcode("mov [{}], {}".format(localsym.memoryaddress, regslice),
                                          "Copy parameter {} to stack".format(param.symbol.name))

                    # allocate space for local variable arrays
                    for symname in block.symboltable.symbols.keys():
                        if block.paramlist.fetch(symname) is None:
                            localsym = block.symboltable.symbols[symname]
                            if isinstance(localsym, Symbol) and not isinstance(localsym, FunctionResultVariableSymbol):
                                if isinstance(localsym.typedef, pascaltypes.ArrayTypeDef):
                                    # TODO - duplicate code from allocating for global arrays, should refactor
                                    self.emitcode("mov rdi, {}".format(localsym.typedef.basetype.numitemsinarray),
                                                  'Allocate memory for local array {}'.format(symname))
                                    self.emitcode(
                                        "mov rsi, {}".format(localsym.typedef.basetype.componenttypedef.basetype.size))
                                    self.emitcode("call _PASCAL_ALLOCATE_MEMORY")
                                    self.emitcode("mov [{}], rax".format(localsym.memoryaddress))

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
                        if isinstance(node.returnval.typedef.basetype, pascaltypes.IntegerType):
                            self.emitcode("mov EAX, [{}]".format(node.returnval.memoryaddress), "set up return value")
                        elif isinstance(node.returnval.typedef.basetype, pascaltypes.BooleanType):
                            # whereas mov EAX, [{}] will zero out the high 32 bits of RAX, moving AL will not.
                            self.emitcode("movzx RAX, BYTE [{}]".format(node.returnval.memoryaddress),
                                          "set up return value")
                        else:
                            self.emitcode("movsd XMM0, [{}]".format(node.returnval.memoryaddress), "set up return val")
                elif isinstance(node, TACUnaryNode):
                    if node.operator == TACOperator.INTTOREAL:
                        assert node.arg1.typedef.basetype.size in [1, 2, 4, 8]
                        if node.arg1.typedef.basetype.size in (1, 2):
                            raise ASMGeneratorError("Cannot handle 8- or 16-bit int convert to real")
                        elif node.arg1.typedef.basetype.size == 4:
                            # extend to 8 bytes
                            self.emit_movtoregister_fromstack("eax", node.arg1)
                            self.emitcode("cdqe")
                        else:
                            self.emit_movtoregister_fromstack("rax", node.arg1)
                        # rax now has the value we need to convert to the float
                        comment = "convert {} to real, store result in {}".format(node.arg1.name, node.lval.name)
                        self.emitcode("cvtsi2sd xmm0, rax", comment)
                        # now save the float into its location
                        # TODO - should this be move xmm register to stack?
                        self.emitcode("movsd [{}], xmm0".format(node.lval.memoryaddress))
                    elif node.operator == TACOperator.ASSIGN:
                        if isinstance(node.lval.typedef, pascaltypes.ArrayTypeDef):
                            assert node.lval.typedef.basetype.size == node.arg1.typedef.basetype.size
                            comment = "Copy array {} into {}".format(node.arg1.name, node.lval.name)
                            self.emit_memcopy(node.lval, node.arg1, node.arg1.typedef.basetype.size, comment, False)
                        else:
                            reg = get_register_slice_bybytes("RAX", node.lval.typedef.basetype.size)
                            # first, get the arg1 into reg.  If arg1 is a byref parameter, we need to
                            # dereference the pointer.
                            comment = "Move {} into {}".format(node.arg1.name, node.lval.name)
                            self.emit_movtoregister_fromstack(reg, node.arg1, comment)
                            if isinstance(node.lval.typedef.basetype, pascaltypes.SubrangeType):
                                # need to validate that the value is in the range before assigning it
                                self.generate_subrangetest_code(reg, node.lval.typedef.basetype)
                            # now, get the value from reg into lval.  If lval is a byref parameter, we
                            # need to dereference the pointer.
                            self.emit_movtostack_fromregister(node.lval, reg)
                    elif node.operator == TACOperator.ASSIGNADDRESSOF:
                        assert isinstance(node.lval.typedef, pascaltypes.PointerTypeDef)
                        comment = "Move address of {} into {}".format(node.arg1.name, node.lval.name)
                        self.emit_movaddresstoregister_fromstack("RAX", node.arg1, comment)
                        self.emit_movtostack_fromregister(node.lval, "RAX")
                    elif node.operator == TACOperator.ASSIGNTODEREF:
                        assert isinstance(node.lval.typedef, pascaltypes.PointerTypeDef)
                        if isinstance(node.arg1.typedef, pascaltypes.ArrayTypeDef):
                            assert node.lval.typedef.pointsto_typedef.basetype.size == node.arg1.typedef.basetype.size
                            comment = "Copy array {} into {}".format(node.arg1.name, node.lval.name)
                            self.emit_memcopy(node.lval, node.arg1, node.arg1.typedef.basetype.size, comment, False)
                        else:
                            comment = "Mov {} to address contained in {}".format(node.arg1.name, node.lval.name)
                            # TODO - handle Real types
                            reg = get_register_slice_bybytes("R11", node.arg1.typedef.basetype.size)
                            self.emit_movtoregister_fromstack(reg, node.arg1, comment)
                            self.emitcode("MOV R10, [{}]".format(node.lval.memoryaddress))
                            self.emitcode("MOV [R10], {}".format(reg))
                    elif node.operator == TACOperator.ASSIGNDEREFTO:
                        assert isinstance(node.arg1.typedef, pascaltypes.PointerTypeDef)
                        comment = "Mov deref of {} to {}".format(node.arg1.name, node.lval.name)
                        destreg = get_register_slice_bybytes("RAX", node.lval.typedef.basetype.size)
                        self.emit_movdereftoregister_fromstack(destreg, node.arg1, comment)
                        self.emit_movtostack_fromregister(node.lval, destreg)
                    elif node.operator == TACOperator.NOT:
                        assert isinstance(node.arg1.typedef.basetype, pascaltypes.BooleanType)
                        assert isinstance(node.lval.typedef.basetype, pascaltypes.BooleanType)
                        self.emit_movtoregister_fromstack("AL", node.arg1)
                        self.emitcode("NOT AL")
                        self.emitcode("AND AL, 0x01")
                        self.emit_movtostack_fromregister(node.lval, "AL")

                    else:  # pragma: no cover
                        raise ASMGeneratorError("Invalid operator: {}".format(node.operator))
                elif isinstance(node, TACUnaryLiteralNode):
                    if isinstance(node.literal1, StringLiteral):
                        # dealing with PEP8 line length
                        glt = self.tacgenerator.globalliteraltable
                        litaddress = glt.fetch(node.literal1.value, pascaltypes.StringLiteralTypeDef()).memoryaddress
                        comment = "Move literal '{}' into {}".format(node.literal1.value, node.lval.name)
                        self.emitcode("lea rax, [rel {}]".format(litaddress), comment)
                        self.emit_movtostack_fromregister(node.lval, "rax")
                    elif isinstance(node.literal1, RealLiteral):
                        glt = self.tacgenerator.globalliteraltable
                        litaddress = glt.fetch(node.literal1.value, pascaltypes.RealLiteralTypeDef()).memoryaddress
                        comment = "Move literal {} into {}".format(node.literal1.value, node.lval.name)
                        self.emitcode("movsd xmm0, [rel {}]".format(litaddress), comment)
                        self.emit_movtostack_fromxmmregister(node.lval, "xmm0")
                    else:
                        if node.operator == TACOperator.ASSIGN:
                            comment = "Move literal '{}' into {}".format(node.literal1.value, node.lval.name)
                            # putting the result into rax so I can use existing helper function vs.
                            # special casing this here.
                            if isinstance(node.literal1, CharacterLiteral):
                                val = ord(node.literal1.value)
                            else:
                                val = node.literal1.value
                            tmpreg = get_register_slice_bybytes("RAX", node.lval.typedef.basetype.size)
                            self.emitcode("mov {}, {}".format(tmpreg, val), comment)
                            self.emit_movtostack_fromregister(node.lval, tmpreg)
                        elif node.operator == TACOperator.INTTOREAL:
                            assert isinstance(node.literal1, IntegerLiteral)
                            comment = "Move integer literal {} into real symbol {}".format(node.literal1.value,
                                                                                           node.lval.name)
                            self.emitcode("MOV EAX, {}".format(node.literal1.value), comment)
                            self.emitcode("CDQE")
                            self.emitcode("cvtsi2sd xmm0, rax")
                            # now save the float into its location
                            self.emit_movtostack_fromxmmregister(node.lval, "xmm0")
                        elif node.operator == TACOperator.ASSIGNTODEREF:
                            assert isinstance(node.lval.typedef, pascaltypes.PointerTypeDef)
                            assert isinstance(node.lval.typedef.pointsto_typedef.basetype, pascaltypes.IntegerType)
                            comment = "Move integer literal {} into address contained in {}"
                            comment = comment.format(node.literal1.value, node.lval.name)
                            # self.emitcode("MOV R11D, {}".format(node.literal1.value), comment)
                            self.emitcode("MOV R10, [{}]".format(node.lval.memoryaddress), comment)
                            self.emitcode("MOV [R10], DWORD {}".format(node.literal1.value))

                        else:
                            print(repr(node.operator))
                            assert False

                elif isinstance(node, TACCallFunctionNode) and \
                        not isinstance(node, TACCallSystemFunctionNode):
                    assert len(params) >= node.numparams
                    localparamlist = params[(-1 * node.numparams):]
                    numintparams = 0
                    numrealparams = 0
                    act_symbol = block.symboltable.parent.fetch(node.funcname)
                    assert isinstance(act_symbol, ActivationSymbol)
                    assert node.numparams == len(act_symbol.paramlist)  # type mismatches are caught upstream

                    # localparamlist has a list of TACParamNodes - that has information of what is going in.
                    # act_symbol.paramlist has the information of where it goes
                    # remove this comment once code is done

                    arrays_to_free_after_proc_call = 0
                    for parampos in range(0, node.numparams):
                        # remember - pointers count as int parameters
                        actualparam = localparamlist[parampos]
                        paramdef = act_symbol.paramlist[parampos]
                        assert isinstance(actualparam, TACParamNode)
                        assert isinstance(paramdef, Parameter)

                        if paramdef.is_byref:
                            comment = "Parameter {} for {} ({}, ByRef)".format(paramdef.symbol.name,
                                                                               act_symbol.name,
                                                                               str(paramdef.symbol.typedef.denoter))
                        else:
                            comment = "Parameter {} for {} ({})".format(paramdef.symbol.name,
                                                                        act_symbol.name,
                                                                        str(paramdef.symbol.typedef.denoter))

                        if paramdef.is_byref and actualparam.paramval.is_byref:
                            # if the formal parameter is byref and actual parameter is byref, then just pass the
                            # value of the actual parameter on through, as that value is a memory address.
                            numintparams += 1
                            assert numintparams <= 6
                            reg = intparampos_to_register(numintparams)
                            self.emitcode("mov {}, [{}]".format(reg, actualparam.paramval.memoryaddress), comment)
                        elif paramdef.is_byref and isinstance(paramdef.symbol.typedef, pascaltypes.ArrayTypeDef):
                            # arrays are already references, so just pass the value of teh actual parameter
                            # on through, exactly same as the case above.
                            numintparams += 1
                            assert numintparams <= 6
                            reg = intparampos_to_register(numintparams)
                            self.emitcode("mov {}, [{}]".format(reg, actualparam.paramval.memoryaddress), comment)
                        elif paramdef.is_byref:
                            numintparams += 1
                            assert numintparams <= 6
                            reg = intparampos_to_register(numintparams)  # we use all 64 bytes for pointers
                            self.emitcode("LEA {}, [{}]".format(reg, actualparam.paramval.memoryaddress), comment)
                        elif isinstance(paramdef.symbol.typedef, pascaltypes.ArrayTypeDef):
                            # need to create a copy of the array and pass that in.
                            pstb = paramdef.symbol.typedef.basetype
                            assert isinstance(pstb, pascaltypes.ArrayType)
                            self.emitcode("PUSH RDI", "create copy of array {}".format(actualparam.paramval.name))
                            self.emitcode("PUSH RSI")
                            self.emitcode("MOV RDI, {}".format(pstb.numitemsinarray))
                            self.emitcode("MOV RSI, {}".format(pstb.componenttypedef.basetype.size))
                            self.emitcode("call _PASCAL_ALLOCATE_MEMORY")
                            self.emitcode("POP RSI")
                            self.emitcode("POP RDI")

                            # rax has the pointer to the memory
                            arrays_to_free_after_proc_call += 1
                            self.emitcode("PUSH RAX", "store address of this array copy to free later")

                            numintparams += 1
                            assert numintparams <= 6
                            reg = intparampos_to_register(numintparams)
                            self.emitcode("MOV {}, RAX".format(reg))
                            self.emit_memcopy(reg, actualparam.paramval, paramdef.symbol.typedef.basetype.size,
                                              "", True)
                        elif isinstance(paramdef.symbol.typedef.basetype, pascaltypes.IntegerType) or \
                                isinstance(paramdef.symbol.typedef.basetype, pascaltypes.BooleanType) or \
                                isinstance(paramdef.symbol.typedef.basetype, pascaltypes.CharacterType) or \
                                isinstance(paramdef.symbol.typedef.basetype, pascaltypes.EnumeratedType):
                            numintparams += 1
                            assert numintparams <= 6  # TODO - remove when we can handle more
                            fullreg = intparampos_to_register(numintparams)
                            reg = get_register_slice_bybytes(fullreg, paramdef.symbol.typedef.basetype.size)
                            self.emit_movtoregister_fromstackorliteral(reg, actualparam.paramval, comment)
                        elif isinstance(paramdef.symbol.typedef.basetype, pascaltypes.RealType):
                            reg = "xmm{}".format(numrealparams)
                            numrealparams += 1
                            assert numrealparams <= 8
                            self.emit_movtoxmmregister_fromstack(reg, actualparam.paramval, comment)
                        else:
                            raise ASMGeneratorError("Invalid Parameter Type")

                    if arrays_to_free_after_proc_call % 2 > 0:
                        self.emitcode("PUSH RAX",
                                      "bogus push to keep stack aligned at 16-bit boundary before function call")

                    self.emitcode("call {}".format(node.label), "call {}()".format(node.funcname))
                    if act_symbol.returntypedef is not None:
                        # return value is now in either RAX or XMM0 - need to store it in right place
                        comment = "assign return value of function to {}".format(node.lval.name)
                        if isinstance(act_symbol.returntypedef.basetype, pascaltypes.IntegerType):
                            self.emitcode("MOV [{}], EAX".format(node.lval.memoryaddress), comment)
                        elif isinstance(act_symbol.returntypedef.basetype, pascaltypes.BooleanType):
                            self.emitcode("MOV [{}], AL".format(node.lval.memoryaddress), comment)
                        else:
                            self.emitcode("MOVSD [{}], XMM0".format(node.lval.memoryaddress), comment)
                    del params[(-1 * node.numparams):]

                    if arrays_to_free_after_proc_call % 2 > 0:
                        self.emitcode("POP RAX", "undo stack-alignment push from above")
                        for i in range(arrays_to_free_after_proc_call):
                            self.emitcode("POP RDI", "free memory from array value parameter")
                            self.emitcode("CALL _PASCAL_DISPOSE_MEMORY")

                elif isinstance(node, TACCallSystemFunctionNode):
                    if node.label.name == "_WRITEI":
                        if node.numparams != 1:  # pragma: no cover
                            raise ASMGeneratorError("Invalid numparams to _WRITEI")
                        self.emitcode("mov rdi, _printf_intfmt")
                        param = params[-1]
                        destregister = get_register_slice_bybytes("RSI", param.paramval.typedef.basetype.size)
                        self.emit_movtoregister_fromstackorliteral(destregister, param.paramval)
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
                    elif node.label.name == "_WRITEC":
                        self.emit_movtoregister_fromstack("RDI", params[-1].paramval)
                        self.emitcode("call putchar wrt ..plt")
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
                        # Currently all of the system functions use a temporary, which I know is not byref.
                        # So, technically it would be quicker to do this:
                        # self.emitcode("MOVSD [{}], XMM0".format(node.lval.memoryaddress), comment)
                        # however, to future-proof this for optimizations, I'll use the movtostack() functions
                        self.emit_movtostack_fromxmmregister(node.lval, "XMM0", comment)
                    elif node.label.name in ("_SINR", "_COSR"):
                        comment = "parameter {} for sin()".format(str(params[-1].paramval))
                        self.emit_movtoxmmregister_fromstack("xmm0", params[-1].paramval, comment)
                        # sin() and cos() use the legacy x87 FPU.  This is slow but also very few instructions
                        # so easy for the compiler writer.  In x86-64 one is supposed to use library functions
                        # for this, but this is faster to code.
                        # Cannot move directly from xmm0 to the FPU stack; cannot move directly from a standard
                        # register to the FPU stack.  Can only move from memory
                        self.emitcode("movsd [{}], xmm0".format(node.lval.memoryaddress),
                                      "use {} to move value to FPU".format(node.lval.name))
                        self.emitcode("fld qword [{}]".format(node.lval.memoryaddress))
                        self.emitcode("f{}".format(node.label.name[1:4]).lower())  # will generate fsin or fcos
                        comment = "assign return value of function to {}".format(node.lval.name)
                        # TODO - see comment to _SQRTR where I use the movtostack() functions.  Technically
                        # there should be a test for node.lval.is_byref here, but for now I know it has to be
                        # a local temporary, not a byref parameter, so this is safe.  I don't want to write
                        # a fstp equivalent for that function when I don't need it.
                        self.emitcode("fstp qword [{}]".format(node.lval.memoryaddress), comment)
                    elif node.label.name == '_LNR':
                        comment = "parameter {} for ln()".format(str(params[-1].paramval))
                        self.emit_movtoxmmregister_fromstack("xmm0", params[-1].paramval, comment)
                        # ln() also uses the legacy x87 FPU.  The legacy FPU has a command for log base 2.
                        # Can get log in any other base from log base 2 by multiplying by the right factor
                        # FYL2X computes the Log base 2 of the value in ST0 and multiplies it by the value
                        # in ST1.  ln(x) = log base 2 of x / log base 2 of e
                        # which in turn equals log base 2 of x * ln 2.
                        self.emitcode("movsd [{}], xmm0".format(node.lval.memoryaddress),
                                      "use {} to move value to FPU".format(node.lval.name))
                        self.emitcode("xorps xmm8, xmm8", "validate parameter is > 0")
                        self.emitcode("ucomisd xmm0, xmm8")
                        self.emitcode("jbe _PASCAL_LN_ERROR")
                        self.emitcode("FLDLN2")
                        self.emitcode("FLD QWORD [{}]".format(node.lval.memoryaddress))
                        self.emitcode("FYL2X")
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emitcode("fstp qword [{}]".format(node.lval.memoryaddress), comment)
                    elif node.label.name == '_EXPR':
                        comment = "parameter {} for exp()".format(str(params[-1].paramval))
                        self.emit_movtoxmmregister_fromstack("xmm0", params[-1].paramval, comment)
                        # exp() also uses the legacy x87 FPU.  The legacy FPU has a command for (2^x)-1.
                        # However, the instruction F2XM1 requires an X between -1 and 1.  Since Pascal EXP() can take
                        # an arbitrary real, this is less desirable.
                        # Let's say that we have a real number.  Represent that number as a + b where a is an integer
                        # and b is the remainder.  e^(a+b) = e^a * e^b where 0 <= b < 1 which is in the range of this
                        # command.
                        # To compute e^b, note that e^b = 2^(log2(e) * b).
                        #       2 ^ (log2(e) * b) = (2^log2(e))^b
                        #       (2^log2(e)) = e
                        #       (2^log2(e)) ^ b = e^b
                        # So call the F2XM1 on b, then add 1 to that, and you get e^b
                        # Need to add that to e^a.  a is an integer, and the FSCALE instruction computes 2^a
                        # See: https://stackoverflow.com/questions/44957136
                        # See: http://www.ray.masmcode.com/tutorial/fpuchap11.htm
                        self.emitcode("movsd [{}], xmm0".format(node.lval.memoryaddress),
                                      "use {} to move value to FPU".format(node.lval.name))
                        self.emitcode("FLDL2E")  # loads log base 2 of e into ST0
                        assert node.lval.typedef.basetype.size in (4, 8)
                        if node.lval.typedef.basetype.size == 4:
                            opsize = "DWORD"
                        else:
                            opsize = "QWORD"
                        self.emitcode("FMUL {} [{}]".format(opsize, node.lval.memoryaddress))  # ST0 contains x*log2(e)
                        self.emitcode("FLD1")  # ST0 now contains 1, ST1 contains x * log2(e)
                        self.emitcode("FLD ST1")  # Pushes a copy of ST1 to the top of the stack.  So now
                                                    # ST0 = x * log2(e), ST1 = 1, and ST2 = x * log2(e)
                        self.emitcode("FPREM1")  # This is clever.  To get the non-integer portion of x * log2(e),
                                                 # we divide it by 1 and take the remainder.  So now
                                                 # ST0 has this remainder, ST1 has 1
                                                 # and ST2 has x * log2(e)
                        self.emitcode("F2XM1")  # now ST0 has (2^remainder) - 1, ST1 has 1, St2 has x * log2(e)
                        self.emitcode("FADDP ST1, ST0")  # this adds ST1 to ST0, pops the stack (moving the 1 into
                                                        # ST0) but then overwrites ST0 with the result.  So
                                                        # ST0 has 2^remainder and ST1 has x * log2(e)
                        self.emitcode("FSCALE")  # Per the fpuchap11.htm link above, FSCALE multiplies ST0 by
                                                 # 2^(ST1), first truncating ST1 to an integer.  It leaves ST1 intact.
                                                 # ST0 has 2^remainder of (x * log2(e)) * 2^integer part of (x*log2(e))
                                                 # So ST0 has e^x in it.  Neat.  ST1 still has x * log2(e) in it.
                        self.emitcode("FSTP ST1")  # We need to clean up the stack, so this gets rid of ST1
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emitcode("fstp qword [{}]".format(node.lval.memoryaddress), comment)
                    elif node.label.name == "_ABSR":
                        # There is an X87 abs() call, but that is slow.  So here is the logic:
                        # To find abs(x) we take x, and compare it to 0-x (which is the negative of x) and then
                        # return whichever is the largest.
                        comment = "parameter {} for abs()".format(str(params[-1].paramval))
                        self.emit_movtoxmmregister_fromstack("xmm0", params[-1].paramval, comment)
                        self.emitcode("xorps xmm8, xmm8")
                        self.emitcode("subsd xmm8, xmm0")
                        self.emitcode("maxsd xmm0, xmm8")
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emit_movtostack_fromxmmregister(node.lval, "XMM0", comment)
                    elif node.label.name == "_ABSI":
                        # There is no X86 ABS() call.  There is a slow way where you test the value, compare to zero
                        # then if it's >= than zero jump ahead, and if it's less than zero, negate it.  Jumps make
                        # code execution very slow.  This is the way CLang 7.0 handles abs() with -O3 enabled
                        comment = "parameter {} for abs()".format(str(params[-1].paramval))
                        self.emit_movtoregister_fromstackorliteral("eax", params[-1].paramval, comment)
                        self.emitcode("mov r11d, eax")
                        self.emitcode("neg eax")  # neg sets the FLAGS
                        self.emitcode("cmovl eax, r11d")  # if neg eax made eax less than zero, move r11d into eax
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emit_movtostack_fromregister(node.lval, "EAX", comment)
                    elif node.label.name == '_ODDI':
                        # per 6.6.6.5 of the ISO Standard, the ODD() function is defined as returning true
                        # if (abs(x) mod 2) = 1.  We could have the TAC simplify ODD into calling ABS but that would
                        # mean two function calls and they are slow.  So for now we will copy the logic for ABS and
                        # mod in here manually.  Note that fortunately the mod equals 0 or 1 at the end, and
                        # that means we do not need a jump test.
                        comment = "parameter {} for odd()".format(str(params[-1].paramval))
                        self.emit_movtoregister_fromstackorliteral("eax", params[-1].paramval, comment)
                        self.emitcode("mov r11d, eax", "odd() is 'if ABS(x) mod 2 == 1")
                        self.emitcode("neg eax")  # neg sets the FLAGS
                        self.emitcode("cmovl eax, r11d")  # if neg eax made eax less than zero, move r11d into eax
                        self.emitcode("cdq", "sign extend eax -> edx:eax")
                        self.emitcode("mov r11d, 2")
                        self.emitcode("idiv r11d")
                        self.emitcode("mov al, dl", "remainder of idiv is in edx; must be 0 or 1. Take lowest 8 bits")
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emit_movtostack_fromregister(node.lval, "AL", comment)
                    elif node.label.name == "_SQRR":
                        # easy - multiply the value by itself
                        # TODO - test for INF since that would be an error, and per ISO standard we need to exit
                        comment = "parameter {} for sqr()".format(str(params[-1].paramval))
                        self.emit_movtoxmmregister_fromstack("xmm0", params[-1].paramval, comment)
                        self.emitcode("mulsd xmm0, xmm0")
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emit_movtostack_fromxmmregister(node.lval, "XMM0", comment)
                    elif node.label.name == "_SQRI":
                        # similarly easy - multiply the value by itself
                        comment = "parameter {} for sqr()".format(str(params[-1].paramval))
                        self.emit_movtoregister_fromstackorliteral("eax", params[-1].paramval, comment)
                        self.emitcode("imul eax, eax")
                        self.emitcode("jo _PASCAL_OVERFLOW_ERROR")
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emit_movtostack_fromregister(node.lval, "EAX", comment)
                    elif node.label.name == "_CHRI":
                        comment = "parameter {} for chr()".format(str(params[-1].paramval))
                        self.emit_movtoregister_fromstackorliteral("R11D", params[-1].paramval, comment)
                        self.emitcode("CMP R11D, 0")
                        self.emitcode("JL _PASCAL_CHR_ERROR")
                        self.emitcode("CMP R11D, 255")
                        self.emitcode("JG _PASCAL_CHR_ERROR")
                        self.emitcode("MOV AL, R11B", "take least significant 8 bits")
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emit_movtostack_fromregister(node.lval, "AL", comment)
                    elif node.label.name == "_ORDO":
                        # Returns the integer representation of the ordinal type.  Since under the covers,
                        # ordinal types are stored as integers, this is just returning itself.
                        # Trick is that the ordinal type may be 1 byte (boolean, character, or user-defined ordinal)
                        # or 4 bytes (integer).  If it's one byte, we need to zero-extend it.
                        assert params[-1].paramval.typedef.basetype.size in (1, 4)

                        comment = "parameter {} for ord()".format(str(params[-1].paramval))
                        if params[-1].paramval.typedef.basetype.size == 1:
                            # TODO - this can easily be done in a single mov statement
                            self.emit_movtoregister_fromstack("R11B", params[-1].paramval, comment)
                            self.emitcode("MOVZX EAX, R11B")
                        else:
                            self.emit_movtoregister_fromstackorliteral("EAX", params[-1].paramval)
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emit_movtostack_fromregister(node.lval, "EAX", comment)
                    elif node.label.name == "_SUCCO":
                        assert params[-1].paramval.typedef.basetype.size in (1, 4)
                        assert node.lval.typedef.basetype.size == params[-1].paramval.typedef.basetype.size
                        comment = "parameter {} for succ()".format(str(params[-1].paramval))
                        reg = get_register_slice_bybytes("RAX", node.lval.typedef.basetype.size)
                        bt = params[-1].paramval.typedef.basetype

                        self.emit_movtoregister_fromstackorliteral(reg, params[-1].paramval, comment)

                        if isinstance(bt, pascaltypes.CharacterType):
                            self.emitcode("CMP {}, 255".format(reg))
                            self.emitcode("JE _PASCAL_SUCC_PRED_ERROR")  # cannot increment a char past 255

                        self.emitcode("INC {}".format(reg))

                        if isinstance(bt, pascaltypes.IntegerType):
                            # todo - we may want to jo every time.  If we have a 1-byte subrange
                            # from something..255, and we succ() when the value is 255, will it get caught
                            self.emitcode("jo _PASCAL_SUCC_PRED_ERROR")
                        elif isinstance(bt, pascaltypes.BooleanType):
                            self.emitcode("CMP {}, 1".format(reg))
                            self.emitcode("JG _PASCAL_SUCC_PRED_ERROR")
                        elif isinstance(bt, pascaltypes.SubrangeType):
                            self.generate_subrangetest_code(reg, bt)
                        elif isinstance(bt, pascaltypes.CharacterType):
                            pass  # did the test for overflow above.
                        else:
                            assert isinstance(bt, pascaltypes.EnumeratedType)
                            self.emitcode("CMP {}, {}".format(reg, str(len(bt.value_list))))
                            self.emitcode("JGE _PASCAL_SUCC_PRED_ERROR")
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emit_movtostack_fromregister(node.lval, reg, comment)
                    elif node.label.name == "_PREDO":
                        assert params[-1].paramval.typedef.basetype.size in (1, 4)
                        assert node.lval.typedef.basetype.size == params[-1].paramval.typedef.basetype.size
                        comment = "parameter {} for pred()".format(str(params[-1].paramval))
                        reg = get_register_slice_bybytes("RAX", node.lval.typedef.basetype.size)

                        self.emit_movtoregister_fromstackorliteral(reg, params[-1].paramval, comment)
                        self.emitcode("DEC {}".format(reg))
                        bt = params[-1].paramval.typedef.basetype
                        if isinstance(bt, pascaltypes.IntegerType):
                            self.emitcode("jo _PASCAL_SUCC_PRED_ERROR")
                        elif isinstance(bt, pascaltypes.SubrangeType):
                            self.generate_subrangetest_code(reg, bt)
                        else:
                            self.emitcode("CMP {}, 0".format(reg))
                            self.emitcode("JL _PASCAL_SUCC_PRED_ERROR")
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emit_movtostack_fromregister(node.lval, reg, comment)
                    elif node.label.name in ("_ROUNDR", "_TRUNCR"):
                        comment = "parameter {} for {}()".format(str(params[-1].paramval), node.label.name[1:6].lower())
                        self.emit_movtoxmmregister_fromstack("xmm0", params[-1].paramval, comment)
                        assert node.lval.typedef.basetype.size in (4, 8)  # can't round into 1 or 2 bytes
                        destreg = get_register_slice_bybytes("RAX", node.lval.typedef.basetype.size)
                        if node.label.name == "_ROUNDR":
                            instruction = "CVTSD2SI"
                        else:
                            instruction = "CVTTSD2SI"
                        # TODO - test for overflow here
                        self.emitcode("{} {}, XMM0".format(instruction, destreg))
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emit_movtostack_fromregister(node.lval, destreg, comment)
                    else:  # pragma: no cover
                        raise ASMGeneratorError("Invalid System Function: {}".format(node.label.name))
                elif isinstance(node, TACBinaryNodeWithBoundsCheck):
                    # currently only used for math with structured types where we have pointers
                    assert isinstance(node.result.typedef, pascaltypes.PointerTypeDef)
                    # only valid binary operation with pointers is addition, when we are accessing
                    # structured types
                    assert node.operator == TACOperator.ADD
                    comment = "{} := {} + {} with bounds check {} to {}"
                    comment = comment.format(node.result.name, node.arg1.name, node.arg2.name, node.lowerbound,
                                             node.upperbound)

                    self.emit_movtoregister_fromstackorliteral("rax", node.arg1, comment)
                    # mov into r11d Automatically zero-extends into r11
                    self.emit_movtoregister_fromstackorliteral("r11d", node.arg2)

                    if isinstance(node.arg2, IntegerLiteral):
                        # bounds-checking should have been done upstream
                        assert node.lowerbound <= int(node.arg2.value) <= node.upperbound
                    else:
                        # if the value in r11d is less than zero, then we tried to add a negative number, which would be
                        # a subscript out of range.
                        self.emitcode("CMP R11D, {}".format(str(node.lowerbound)))
                        self.emitcode("JL _PASCAL_ARRAYINDEX_ERROR")

                        # we are only adding to pointers that point to arrays.  Not adding to pointers in the middle
                        # of arrays.  And the addition is always a multiple of the size of the component type.
                        # So, if the number of bytes being added is greater than the size allocated to the pointer,
                        # we have gone over and this would be an index error
                        # TODO - assert someplace that when we're adding we're adding the right multiple.
                        self.emitcode("CMP R11D, {}".format(str(node.upperbound)))
                        self.emitcode("JG _PASCAL_ARRAYINDEX_ERROR")

                    self.emitcode("add rax, r11")
                    self.emitcode("jo _PASCAL_OVERFLOW_ERROR")
                    self.emit_movtostack_fromregister(node.result, "rax")

                elif isinstance(node, TACBinaryNode):

                    assert isinstance(node.result.typedef.basetype, pascaltypes.IntegerType) or \
                            isinstance(node.result.typedef.basetype, pascaltypes.BooleanType) or \
                            isinstance(node.result.typedef.basetype, pascaltypes.RealType)

                    comment = "{} := {} {} {}".format(node.result.name, node.arg1.name, node.operator, node.arg2.name)

                    if isinstance(node.result.typedef.basetype, pascaltypes.IntegerType):
                        # TODO - handle something other than 4-byte integers
                        if node.operator in (TACOperator.MULTIPLY, TACOperator.ADD, TACOperator.SUBTRACT):
                            if node.operator == TACOperator.MULTIPLY:
                                op = "imul"
                            elif node.operator == TACOperator.ADD:
                                op = "add"
                            else:
                                op = "sub"

                            self.emit_movtoregister_fromstackorliteral("eax", node.arg1, comment)
                            self.emit_movtoregister_fromstackorliteral("r11d", node.arg2)
                            self.emitcode("{} eax, r11d".format(op))
                            self.emitcode("jo _PASCAL_OVERFLOW_ERROR")
                            self.emit_movtostack_fromregister(node.result, "eax")

                        elif node.operator in (TACOperator.IDIV, TACOperator.MOD):
                            self.emit_movtoregister_fromstackorliteral("eax", node.arg1, comment)
                            self.emit_movtoregister_fromstackorliteral("r11d", node.arg2)

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
                    elif isinstance(node.result.typedef.basetype, pascaltypes.RealType):
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

                    else:
                        assert isinstance(node.result.typedef.basetype, pascaltypes.BooleanType)
                        n1type = node.arg1.typedef.basetype
                        n2type = node.arg2.typedef.basetype

                        if not block.symboltable.are_compatible(n1type.typename, n2type.typename):  # pragma: no cover
                            raise ASMGeneratorError("Cannot mix {} and {} with relational operator".format(str(n1type),
                                                                                                           str(n2type)))

                        if node.operator in (TACOperator.AND, TACOperator.OR):
                            assert isinstance(n1type, pascaltypes.BooleanType)
                            assert isinstance(n2type, pascaltypes.BooleanType)
                            self.emit_movtoregister_fromstack("al", node.arg1, comment)
                            self.emit_movtoregister_fromstack("r11b", node.arg2)
                            if node.operator == TACOperator.AND:
                                self.emitcode("and al, r11b")
                            else:
                                self.emitcode("or al, r11b")
                            self.emit_movtostack_fromregister(node.result, "AL")
                        else:
                            if isinstance(n1type, pascaltypes.BooleanType) or \
                                    isinstance(n1type, pascaltypes.IntegerType) or \
                                    is_integerorboolean_subrangetype(n1type):
                                # TODO: Handling String types in relational operators

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
                            else:
                                assert isinstance(n1type, pascaltypes.RealType) or \
                                    isinstance(n1type, pascaltypes.CharacterType) or \
                                    isinstance(n1type, pascaltypes.EnumeratedType) or \
                                    isinstance(n1type, pascaltypes.SubrangeType)
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

                            if isinstance(n1type, pascaltypes.IntegerType) or \
                                    (isinstance(n1type, pascaltypes.SubrangeType) and
                                     n1type.hosttypedef.basetype.size == 4):
                                self.emit_movtoregister_fromstackorliteral("eax", node.arg1, comment)
                                self.emit_movtoregister_fromstackorliteral("r11d", node.arg2)
                                self.emitcode("cmp eax, r11d")
                            elif isinstance(n1type, pascaltypes.BooleanType) or \
                                    isinstance(n1type, pascaltypes.CharacterType) or \
                                    isinstance(n1type, pascaltypes.EnumeratedType) or \
                                    (isinstance(n1type, pascaltypes.SubrangeType) and
                                     n1type.hosttypedef.basetype.size == 1):
                                self.emit_movtoregister_fromstack("al", node.arg1, comment)
                                self.emit_movtoregister_fromstack("r11b", node.arg2)
                                self.emitcode("cmp al, r11b")
                            else:  # has to be real; we errored above if any other type
                                assert isinstance(n1type, pascaltypes.RealType)
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
                    raise ASMGeneratorError("Unknown TAC node type: {}".format(type(node)))

            if totalstorageneeded > 0 or block.ismain:
                self.emitcode("MOV RSP, RBP", "restore stack pointer")
                self.emitcode("POP RBP")
            if block.ismain:
                # deallocate global arrays
                # TODO: refactor this loop to be something like "get global array symbols" or something
                for symname in self.tacgenerator.globalsymboltable.symbols.keys():
                    sym = self.tacgenerator.globalsymboltable.fetch(symname)
                    if isinstance(sym, Symbol) and isinstance(sym.typedef, pascaltypes.ArrayTypeDef):
                        self.emitcode("mov rdi, [{}]".format(sym.memoryaddress),
                                      "Free memory for global array {}".format(symname))
                        self.emitcode("call _PASCAL_DISPOSE_MEMORY")
            else:
                # deallocate local arrays
                for symname in block.symboltable.symbols.keys():
                    if block.paramlist.fetch(symname) is None:
                        localsym = block.symboltable.symbols[symname]
                        if isinstance(localsym, Symbol) and not isinstance(localsym, FunctionResultVariableSymbol):
                            if isinstance(localsym.typedef, pascaltypes.ArrayTypeDef):
                                self.emitcode("mov rdi, [{}]".format(localsym.memoryaddress),
                                              "Free memory for local array {}".format(symname))
                                self.emitcode("call _PASCAL_DISPOSE_MEMORY")
                self.emitcode("RET")

    def generate_helperfunctioncode(self):
        # TODO - optimize so we only include code if features needing it are in the asm code
        # TODO - consider moving functions into ASM files so we can build ASM unit tests.
        self.emitlabel("_PASCAL_ALLOCATE_MEMORY")
        self.emitcomment("takes a number of members (RDI) and a size (RSI)")
        self.emitcomment("returns pointer to memory in RAX.")
        # just a passthrough for CALLOC
        # yes, calloc() initializes memory and Pascal is not supposed to do so, but calloc() is safer
        # in that it tests for an overflow when you multiply nmemb * size whereas malloc() does not.
        self.emitcode("call calloc wrt ..plt")
        self.emitcode("test rax, rax")
        self.emitcode("jle _PASCAL_CALLOC_ERROR")
        self.emitcode("ret")
        self.emitlabel("_PASCAL_DISPOSE_MEMORY")
        self.emitcomment("takes a pointer to memory (RDI)")
        # just a passthrough for FREE
        self.emitcode("call free wrt ..plt")
        self.emitcode("test rax, rax")
        self.emitcode("jl _PASCAL_DISPOSE_ERROR")
        self.emitcode("ret")

    def generate_errorhandlingcode(self):
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
        self.emitlabel("_PASCAL_CHR_ERROR")
        self.emitcode("mov rdi, _stringerr_5")
        self.emitcode("jmp _PASCAL_PRINT_ERROR")
        self.emitlabel("_PASCAL_SUCC_PRED_ERROR")
        self.emitcode("mov rdi, _stringerr_6")
        self.emitcode("jmp _PASCAL_PRINT_ERROR")
        self.emitlabel("_PASCAL_SUBRANGE_ERROR")
        self.emitcode("mov rdi, _stringerr_7")
        self.emitcode("jmp _PASCAL_PRINT_ERROR")
        self.emitlabel("_PASCAL_ARRAYINDEX_ERROR")
        self.emitcode("mov rdi, _stringerr_8")
        self.emitcode("jmp _PASCAL_PRINT_ERROR")
        self.emitlabel("_PASCAL_CALLOC_ERROR")
        self.emitcode("mov rdi, _stringerr_9")
        self.emitcode("jmp _PASCAL_PRINT_ERROR")
        self.emitlabel("_PASCAL_DISPOSE_ERROR")
        self.emitcode("mov rdi, _stringerr_10")
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
        self.generate_helperfunctioncode()
        self.generate_errorhandlingcode()

    def generate_bsssection(self):
        if len(self.tacgenerator.globalsymboltable.symbols.keys()) > 0:
            self.emitsection("bss")
            varseq = 0
            for symname in self.tacgenerator.globalsymboltable.symbols.keys():
                sym = self.tacgenerator.globalsymboltable.fetch(symname)
                if isinstance(sym, Symbol):
                    if not isinstance(sym, ActivationSymbol):
                        label = "_globalvar_{}".format(str(varseq))
                        varseq += 1
                        sym.memoryaddress = "rel {}".format(label)
                        if isinstance(sym.typedef, pascaltypes.ArrayTypeDef):
                            self.emitcode("{} resb 8".format(label),
                                          "address for global array variable {}".format(symname))
                        else:
                            self.emitcode("{} resb {}".format(label, sym.typedef.basetype.size),
                                          "global variable {}".format(symname))

    def generate(self, objfilename, exefilename):
        self.generate_externs()
        self.generate_bsssection()
        self.generate_datasection()
        self.generate_textsection()
        self.asmfile.close()
        os.system("nasm -f elf64 -F dwarf -g -o {} {}".format(objfilename, self.asmfilename))
        os.system("gcc {} -o {}".format(objfilename, exefilename))
