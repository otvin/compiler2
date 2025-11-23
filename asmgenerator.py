import os
from tac_ir import TACBlock, TACLabelNode, TACParamNode, TACCallSystemFunctionNode, TACUnaryLiteralNode, \
    TACOperator, TACGenerator, TACCommentNode, TACBinaryNode, TACUnaryNode, TACGotoNode, TACIFZNode, \
    TACFunctionReturnNode, TACCallFunctionNode, TACBinaryNodeWithBoundsCheck
from symboltable import StringLiteral, IntegerLiteral, Symbol, Parameter, ActivationSymbol, RealLiteral, \
    FunctionResultVariableSymbol, CharacterLiteral, ConstantSymbol, ProgramParameterSymbol
from compiler_error import compiler_errstr, compiler_failstr
from editor_settings import NUM_SPACES_IN_TAB, NUM_TABS_FOR_COMMENT
import pascaltypes


class ASMGeneratorError(Exception):
    pass


VALID_REGISTER_LIST = ["RAX", "RBX", "RCX", "RDX", "RSI", "RDI", "RBP", "RSP", "R8", "R9", "R10", "R11", "R12",
                       "R13", "R14", "R15", "R16"]

VALID_DWORD_REGISTER_LIST = ["EAX", "EBX", "ECX", "EDX", "ESI", "EDI", "EBP", "ESP", "R8D", "R9D", "R10D", "R11D",
                             "R12D", "R13D", "R14D", "R15D", "R16D"]

VALID_SCRATCH_REGISTER_LIST = ["R11", "R10", "R15", "R16"]  # TODO - Validate this list with the ABI

FILESTATE_NOTINITIALIZED = 0
FILESTATE_GENERATION = 1
FILESTATE_INSPECTION = 2


class PascalError:
    def __init__(self, errorstr, label, isused=False):
        # we will only write the error information to the .asm file if it is invoked someplace
        assert isinstance(errorstr, str)
        assert isinstance(label, str)
        self.isused = isused
        self.errorstr = errorstr
        self.label = label


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
        if isinstance(basetype.hosttype, pascaltypes.IntegerType):
            ret = True
        elif isinstance(basetype.hosttype, pascaltypes.BooleanType):
            ret = True
    return ret


class AssemblyGenerator:
    def __init__(self, asmfilename, tacgenerator):
        assert isinstance(tacgenerator, TACGenerator)
        self.asmfilename = asmfilename
        self.asmfile = open(asmfilename, 'w')
        self.tacgenerator = tacgenerator
        self.maxlabelnum = 0
        self.pascalerrors = {}
        self.init_pascalerrors()
        self.used_x87_code = False
        self.used_calloc = False
        self.used_dispose = False

    def init_pascalerrors(self):

        # Overflow error is referenced in compiler2_system_io.asm and compiler2_stringcompare.asm
        self.pascalerrors[0] = PascalError("Overflow error", "_PASCAL_OVERFLOW_ERROR", True)
        self.pascalerrors[1] = PascalError("Error D.44 or D.45: Division by zero error", "_PASCAL_DIVZERO_ERROR")
        self.pascalerrors[2] = PascalError("Error D.46: Divisor in Mod must be positive", "_PASCAL_MOD_ERROR")
        self.pascalerrors[3] = PascalError("Error D.34: Cannot take sqrt() of negative number", "_PASCAL_SQRT_ERROR")
        self.pascalerrors[4] = PascalError("Error D.33: Cannot take ln() of number less than or equal to zero",
                                           "_PASCAL_LN_ERROR")
        self.pascalerrors[5] = PascalError("Error D.37: value to chr() exceeds 0-255 range for Char type",
                                           "_PASCAL_CHR_ERROR")
        self.pascalerrors[6] = PascalError("Error D.38 or D.39: succ() or pred() exceeds range for enumerated type",
                                           "_PASCAL_SUCC_PRED_ERROR")
        self.pascalerrors[7] = PascalError("Error: value exceeds range for subrange type", "_PASCAL_SUBRANGE_ERROR")
        self.pascalerrors[8] = PascalError("Error: array index out of range.", "_PASCAL_ARRAYINDEX_ERROR")
        self.pascalerrors[9] = PascalError("Error: dynamic memory allocation failed.", "_PASCAL_CALLOC_ERROR")
        self.pascalerrors[10] = PascalError("Error: unable to de-allocate dynamic memory.", "_PASCAL_DISPOSE_ERROR")
        # D.14 is referenced in compiler2_system_io.asm
        self.pascalerrors[11] = PascalError("Error D.14: file not in inspection mode prior to get() or read().",
                                            "_PASCAL_WRONGMODE_GET_ERROR", True)
        # D.16 is referenced in compiler2_system_io.asm
        self.pascalerrors[12] = PascalError("Error D.16: EOF encountered during get() or read().",
                                            "_PASCAL_EOF_GET_ERROR", True)
        self.pascalerrors[13] = PascalError(
            "Error D.9: File not in generation mode prior to put(), write(), writeln(), or page().",
            "_PASCAL_FILENOTGENERATION_ERROR")
        self.pascalerrors[14] = PascalError("Error D.14: File not in inspection mode prior to get() or read().",
                                            "_PASCAL_FILENOTINSPECTION_ERROR")
        self.pascalerrors[15] = PascalError("Error D.10 or D.15: File undefined prior to access.",
                                            "_PASCAL_UNDEFINEDFILE_ERROR")
        self.pascalerrors[16] = PascalError("Error: insufficient number of command-line arguments.",
                                            "_PASCAL_INSUFFICIENT_ARGC_ERROR")
        self.pascalerrors[17] = PascalError("Error opening file.", "_PASCAL_FOPEN_ERROR")
        self.pascalerrors[18] = PascalError("Error D.48: Activation of function is undefined upon function completion.",
                                            "_PASCAL_NORETURNVAL_ERROR")

    def emit(self, s):
        self.asmfile.write(s)

    def emitln(self, s):
        self.emit(s + '\n')

    def emitcode(self, s, comment=None):
        if comment is None:
            self.emitln('\t' + s)
        else:
            numtabs = NUM_TABS_FOR_COMMENT - 1 - (len(s) // NUM_SPACES_IN_TAB)
            if numtabs < 0:  # pragma: no cover
                numtabs = 0
            tabstr = "\t" * numtabs
            self.emitln('\t' + s + tabstr + ';' + comment)

    def emitlabel(self, labelname, comment=None):
        if comment is None:
            self.emitln(labelname + ":")
        else:
            numtabs = NUM_TABS_FOR_COMMENT - (len(labelname) // NUM_SPACES_IN_TAB)
            if numtabs < 0:  # pragma: no cover
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

        if destreg.upper() in VALID_DWORD_REGISTER_LIST and symbol.pascaltype.size == 1:
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
        assert isinstance(symbol, Symbol), type(symbol)
        if symbol.is_byref:
            self.emitcode("mov r10, [{}]".format(symbol.memoryaddress), comment)
            self.emitcode("movsd {}, [r10]".format(destreg))
        else:
            self.emitcode("movsd {}, [{}]".format(destreg, symbol.memoryaddress), comment)

    def emit_movaddresstoregister_fromstack(self, destreg, symbol, comment=None):
        assert isinstance(symbol, Symbol)
        if symbol.is_byref or isinstance(symbol.pascaltype, pascaltypes.ArrayType):
            self.emitcode("mov {}, [{}]".format(destreg, symbol.memoryaddress), comment)
        else:
            # never been tested
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
        assert not symbol.is_byref  # if it's byref, it will not be passed in an xmm register
        self.emitcode("movsd [{}], {}".format(symbol.memoryaddress, sourcereg), comment)

    def emit_jumptoerror(self, jump_mnemonic, errorlabel):
        # If there were thousands of errors, this would be slow, but there aren't
        assert isinstance(jump_mnemonic, str)
        assert jump_mnemonic[0].lower() == 'j'  # all jump instructions begin with j
        assert isinstance(errorlabel, str)

        foundit = False
        for i in self.pascalerrors.keys():
            if self.pascalerrors[i].label == errorlabel:
                self.pascalerrors[i].isused = True
                foundit = True
                break
        assert foundit  # if it's not a valid error code we have a typo
        self.emitcode("{} {}".format(jump_mnemonic, errorlabel))

    def emit_memcopy(self, destsym, sourcesym, numbytes, comment="", preserve_regs=False):
        # the memcopy uses rdi, rsi, and rcx.  If preserve_regs is true, we will push/pop them to ensure
        # they are in same state as they were on entry

        # this is a bit hacky - sometimes I have a destination symbol, sometimes a register.  Since Python is
        # not statically typed, I can have one function handle either type of input, but it may not be very clean.

        assert isinstance(sourcesym, Symbol)
        assert isinstance(destsym, Symbol) or (isinstance(destsym, str) and destsym.upper() in VALID_REGISTER_LIST)
        assert numbytes > 0
        assert isinstance(sourcesym.pascaltype, pascaltypes.PointerType) or \
               isinstance(sourcesym.pascaltype, pascaltypes.ArrayType) or \
               isinstance(sourcesym.pascaltype, pascaltypes.StringLiteralType)

        if isinstance(destsym, Symbol):
            assert isinstance(destsym.pascaltype, pascaltypes.PointerType) or \
                   isinstance(destsym.pascaltype, pascaltypes.ArrayType)

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
        self.emitcode("extern fprintf")
        self.emitcode("extern fopen")
        self.emitcode("extern freopen")
        self.emitcode("extern fputc")
        self.emitcode("extern calloc")
        self.emitcode("extern free")
        self.emitcode("extern fflush")
        self.emitcode("extern stdout")

        self.emitcode("extern _PASCAL_PRINTSTRINGTYPE", "from compiler2_system_io.asm")
        self.emitcode("extern _PASCAL_GETC", "from compiler2_system_io.asm")
        self.emitcode("extern _PASCAL_STRINGCOMPARE", "from compiler2_stringcompare.asm")

        self.emitcode("global _PASCAL_OVERFLOW_ERROR", "needed by compiler2_*.asm")
        self.emitcode("global _PASCAL_WRONGMODE_GET_ERROR")
        self.emitcode("global _PASCAL_EOF_GET_ERROR")

    def generate_datasection(self):
        self.emitsection("data")
        self.emitcomment("error handling strings")
        for i in self.pascalerrors.keys():
            # TODO - we could iterate over all the TACBlocks, identify which errors we will need, then change
            # emit_jumptoerror to test whether or not we're invoking an error that we have marked as used.  That
            # would reduce the binary size.
            self.emitcode('_pascalerr_{} db `{}`, 0'.format(str(i), self.pascalerrors[i].errorstr))
        self.emitcomment("support for write() commands")
        self.emitcode('_printf_intfmt db "%d",0')
        # TODO - this is not pascal-compliant, as should be fixed characters right-justified
        # but is better than the C default of 6 digits to the right of the decimal.
        self.emitcode('_printf_realfmt db "%.12f",0')
        self.emitcode('_printf_newln db 10,0')
        self.emitcode('_printf_true db "TRUE",0')
        self.emitcode('_printf_false db "FALSE",0')

        self.emitcode('_filemode_write db "w",0')
        self.emitcode('_filemode_writebinary db "wb",0')
        self.emitcode('_filemode_read db "r",0')
        self.emitcode('_filemode_readbinary db "rb",0')

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
                        errstr = compiler_errstr("String literal '{}' exceeds 255 char max length.".format(lit.value),
                                                 None, lit.location)
                        raise ASMGeneratorError(errstr)
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
        if subrange_basetype.size == 1:
            # single-byte subranges use unsigned comparisons; integer (4-byte) subranges use signed comparisons.
            jumpless = "JB"
            jumpgreater = "JA"
        else:
            jumpless = "JL"
            jumpgreater = "JG"

        comment = "Validate we are within proper range"
        self.emitcode("CMP {}, {}".format(reg, subrange_basetype.rangemin_int), comment)
        self.emit_jumptoerror(jumpless, "_PASCAL_SUBRANGE_ERROR")
        self.emitcode("CMP {}, {}".format(reg, subrange_basetype.rangemax_int))
        self.emit_jumptoerror(jumpgreater, "_PASCAL_SUBRANGE_ERROR")

    def generate_parameter_comments(self, block):
        assert isinstance(block, TACBlock)
        for param in block.paramlist:
            localsym = block.symboltable.fetch(param.symbol.name)
            self.emitcomment("Parameter {} - [{}]".format(param.symbol.name, localsym.memoryaddress), True)

    def generate_localvar_comments(self, block):
        assert isinstance(block, TACBlock)
        for symname in block.symboltable.symbols.keys():
            if block.ismain or block.paramlist.fetch(symname) is None:
                localsym = block.symboltable.symbols[symname]
                if isinstance(localsym, Symbol):
                    if isinstance(localsym, FunctionResultVariableSymbol):
                        self.emitcomment("Function Result - [{}]".format(localsym.memoryaddress), True)
                    else:
                        self.emitcomment("Local Variable {} - [{}]".format(symname, localsym.memoryaddress), True)

    def generate_array_variable_memory_allocation_code(self, sym):
        assert isinstance(sym, Symbol)
        assert isinstance(sym.pascaltype, pascaltypes.ArrayType)
        self.emitcode("mov rdi, {}".format(sym.pascaltype.numitemsinarray),
                      'Allocate memory for array {}'.format(sym.name))
        self.emitcode("mov rsi, {}".format(sym.pascaltype.componenttype.size))
        self.used_calloc = True
        self.emitcode("call _PASCAL_ALLOCATE_MEMORY")
        self.emitcode("mov [{}], rax".format(sym.memoryaddress))

    def generate_paramlist_to_stack_code(self, block):
        assert isinstance(block, TACBlock)
        numintparams = 0
        numrealparams = 0
        for param in block.paramlist:
            localsym = block.symboltable.fetch(param.symbol.name)
            # TODO - this will break when we have so many parameters that they will get
            # passed on the stack instead of in a register.
            if isinstance(param.symbol.pascaltype, pascaltypes.ArrayType):
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

    def generate_procfunc_call_code(self, block, node, params):
        assert isinstance(block, TACBlock)
        assert isinstance(node, TACCallFunctionNode)
        assert not isinstance(node, TACCallSystemFunctionNode)
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
                                                                   str(paramdef.symbol.pascaltype.identifier))
            else:
                comment = "Parameter {} for {} ({})".format(paramdef.symbol.name,
                                                            act_symbol.name,
                                                            str(paramdef.symbol.pascaltype.identifier))

            if paramdef.is_byref and actualparam.paramval.is_byref:
                # if the formal parameter is byref and actual parameter is byref, then just pass the
                # value of the actual parameter on through, as that value is a memory address.
                numintparams += 1
                assert numintparams <= 6
                reg = intparampos_to_register(numintparams)
                self.emitcode("mov {}, [{}]".format(reg, actualparam.paramval.memoryaddress), comment)
            elif paramdef.is_byref and isinstance(paramdef.symbol.pascaltype, pascaltypes.ArrayType):
                # arrays are already references, so just pass the value of the actual parameter
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
            elif isinstance(paramdef.symbol.pascaltype, pascaltypes.ArrayType):
                # need to create a copy of the array and pass that in.
                # TODO - use this psp before the if statement, or remove it from here, as lots of references below
                psp = paramdef.symbol.pascaltype
                assert isinstance(psp, pascaltypes.ArrayType)
                self.emitcode("PUSH RDI", "create copy of array {}".format(actualparam.paramval.name))
                self.emitcode("PUSH RSI")
                self.emitcode("MOV RDI, {}".format(psp.numitemsinarray))
                self.emitcode("MOV RSI, {}".format(psp.componenttype.size))
                self.used_calloc = True
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
                self.emit_memcopy(reg, actualparam.paramval, paramdef.symbol.pascaltype.size,
                                  "", True)
            elif isinstance(paramdef.symbol.pascaltype, pascaltypes.IntegerType) or \
                    isinstance(paramdef.symbol.pascaltype, pascaltypes.BooleanType) or \
                    isinstance(paramdef.symbol.pascaltype, pascaltypes.CharacterType) or \
                    isinstance(paramdef.symbol.pascaltype, pascaltypes.SubrangeType) or \
                    isinstance(paramdef.symbol.pascaltype, pascaltypes.EnumeratedType):
                numintparams += 1
                assert numintparams <= 6  # TODO - remove when we can handle more
                fullreg = intparampos_to_register(numintparams)
                reg = get_register_slice_bybytes(fullreg, paramdef.symbol.pascaltype.size)
                self.emit_movtoregister_fromstackorliteral(reg, actualparam.paramval, comment)
            elif isinstance(paramdef.symbol.pascaltype, pascaltypes.RealType):
                reg = "xmm{}".format(numrealparams)
                numrealparams += 1
                assert numrealparams <= 8
                self.emit_movtoxmmregister_fromstack(reg, actualparam.paramval, comment)
            else:  # pragma: no cover
                raise ASMGeneratorError("Invalid Parameter Type")

        if arrays_to_free_after_proc_call % 2 > 0:
            self.emitcode("PUSH RAX",
                          "bogus push to keep stack aligned at 16-bit boundary before function call")

        self.emitcode("call {}".format(node.label), "call {}()".format(node.funcname))
        if act_symbol.returntype is not None:
            # Need to insert code for the runtime error for function with undefined returnval
            self.pascalerrors[18].isused = True

            # return value is now in either RAX or XMM0 - need to store it in right place
            comment = "assign return value of function to {}".format(node.lval.name)
            if isinstance(act_symbol.returntype, pascaltypes.IntegerType):
                self.emitcode("MOV [{}], EAX".format(node.lval.memoryaddress), comment)
            elif isinstance(act_symbol.returntype, pascaltypes.BooleanType):
                self.emitcode("MOV [{}], AL".format(node.lval.memoryaddress), comment)
            else:
                self.emitcode("MOVSD [{}], XMM0".format(node.lval.memoryaddress), comment)
        del params[(-1 * node.numparams):]

        if arrays_to_free_after_proc_call % 2 > 0:
            self.emitcode("POP RAX", "undo stack-alignment push from above")
            for i in range(arrays_to_free_after_proc_call):
                self.emitcode("POP RDI", "free memory from array value parameter")
                self.used_dispose = True
                self.emitcode("CALL _PASCAL_DISPOSE_MEMORY")

    def generate_filevariable_statevalidationcode(self, filesym, state):
        global FILESTATE_GENERATION
        global FILESTATE_INSPECTION
        global FILESTATE_NOTINITIALIZED
        assert isinstance(filesym, Symbol)
        assert isinstance(filesym.pascaltype, pascaltypes.FileType)
        assert state in (FILESTATE_GENERATION, FILESTATE_INSPECTION)

        # current state of the file is in the 9th byte after the location of the file
        self.emitcode("lea rax, [{}]".format(filesym.memoryaddress), "validate file state")
        self.emitcode("add rax, 8")
        self.emitcode("mov r11b, byte [rax]")
        self.emitcode("test r11b, r11b")
        self.emit_jumptoerror("jz", "_PASCAL_UNDEFINEDFILE_ERROR")
        self.emitcode("cmp r11b, {}".format(str(state)))
        if state == FILESTATE_GENERATION:
            self.emit_jumptoerror("jne", "_PASCAL_FILENOTGENERATION_ERROR")
        else:
            self.emit_jumptoerror("jne", "_PASCAL_FILENOTINSPECTION_ERROR")

    def generate_programparameter_initializationcode(self):
        # assumption:
        # RDI - contains int argc (integer with number parameters)
        # RSI - contains char **argv

        symlist = []

        for symname in self.tacgenerator.globalsymboltable.symbols.keys():
            sym = self.tacgenerator.globalsymboltable.fetch(symname)
            if isinstance(sym, ProgramParameterSymbol) and sym.name not in ("input", "output"):
                symlist.append((sym.position, sym.filenamememoryaddress, sym.name))

        if len(symlist) > 0:
            self.emitcode("cmp RDI, {}".format(len(symlist)), "Test number of command-line arguments")
            self.emit_jumptoerror("jl", "_PASCAL_INSUFFICIENT_ARGC_ERROR")
            for syminfo in symlist:
                rsi_offset = 8 * syminfo[0]
                comment = "retrieve file name for variable {}".format(syminfo[2])
                self.emitcode("mov RAX, [RSI+{}]".format(rsi_offset), comment)
                self.emitcode("mov [{}], rax".format(syminfo[1]))

    def generate_globalfile_initializationcode(self):
        # set up stdin and stdout if needed
        for symname in self.tacgenerator.globalsymboltable.symbols.keys():
            sym = self.tacgenerator.globalsymboltable.fetch(symname)
            if isinstance(sym, ProgramParameterSymbol):

                if sym.name == "output":
                    stdinout = "stdout"
                    start_filestate = FILESTATE_GENERATION
                elif sym.name == "input":
                    stdinout = "stdin"
                    start_filestate = FILESTATE_INSPECTION
                else:
                    stdinout = ""
                    start_filestate = FILESTATE_NOTINITIALIZED

                if sym.name in ("input", "output"):
                    comment = "initialize global textfile variable '{}'".format(sym.name)
                    self.emitcode("lea r11, [rel {}]".format(stdinout), comment)
                    self.emitcode("mov rax, [r11]")
                    self.emitcode("mov [{}], rax".format(sym.memoryaddress))

                self.emitcode("lea rax, [{}]".format(sym.memoryaddress))
                self.emitcode("add rax, 8")
                self.emitcode("mov [rax], byte {}".format(start_filestate))
                self.emitcode("inc rax")
                self.emitcode("mov [rax], byte 0")

    def generate_code(self):
        params = []  # this is a stack of parameters

        for block in self.tacgenerator.tacblocks:
            assert isinstance(block, TACBlock)

            if block.ismain:
                self.emitlabel("main")
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
                    if isinstance(sym, ProgramParameterSymbol) and sym.name not in ("input", "output"):
                        totalstorageneeded += 8

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
                    self.generate_parameter_comments(block)
                    self.generate_localvar_comments(block)
                    self.generate_paramlist_to_stack_code(block)

                    # allocate space for local variable arrays
                    for symname in block.symboltable.symbols.keys():
                        if block.paramlist.fetch(symname) is None:
                            localsym = block.symboltable.symbols[symname]
                            if isinstance(localsym, Symbol) and not isinstance(localsym, FunctionResultVariableSymbol):
                                if isinstance(localsym.pascaltype, pascaltypes.ArrayType):
                                    self.generate_array_variable_memory_allocation_code(localsym)

                else:
                    self.generate_localvar_comments(block)
                    # This needs to be first because it takes advantage of RDI and RSI state when execution starts
                    self.generate_programparameter_initializationcode()
                    self.generate_globalfile_initializationcode()
                    if self.used_x87_code:
                        self.emitcode("finit")
                    # need to init any global variables that are arrays
                    for symname in self.tacgenerator.globalsymboltable.symbols.keys():
                        sym = self.tacgenerator.globalsymboltable.fetch(symname)
                        if isinstance(sym, Symbol) and isinstance(sym.pascaltype, pascaltypes.ArrayType):
                            self.generate_array_variable_memory_allocation_code(sym)

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
                        # TODO - Detect if the return value was not set, and error if it wasn't.
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
                        assert node.arg1.pascaltype.size in [1, 2, 4, 8]
                        if node.arg1.pascaltype.size in (1, 2):
                            raise ASMGeneratorError("Cannot handle 8- or 16-bit int convert to real")
                        elif node.arg1.pascaltype.size == 4:
                            # extend to 8 bytes
                            self.emit_movtoregister_fromstack("eax", node.arg1)
                            self.emitcode("cdqe")
                        else:
                            self.emit_movtoregister_fromstack("rax", node.arg1)
                        # rax now has the value we need to convert to the float
                        comment = "convert {} to real, store result in {}".format(node.arg1.name, node.lval.name)
                        self.emitcode("cvtsi2sd xmm0, rax", comment)
                        # now save the float into its location
                        self.emit_movtostack_fromxmmregister(node.lval, "xmm0")
                    elif node.operator == TACOperator.ASSIGN:
                        if isinstance(node.lval.pascaltype, pascaltypes.ArrayType):
                            assert node.lval.pascaltype.size == node.arg1.pascaltype.size or \
                                   (node.lval.pascaltype.is_string_type() and
                                    isinstance(node.arg1.pascaltype, pascaltypes.StringLiteralType))
                            comment = "Copy array {} into {}".format(node.arg1.name, node.lval.name)
                            self.emit_memcopy(node.lval, node.arg1, node.lval.pascaltype.size, comment, False)
                        else:
                            reg = get_register_slice_bybytes("RAX", node.lval.pascaltype.size)
                            # first, get the arg1 into reg.  If arg1 is a byref parameter, we need to
                            # dereference the pointer.
                            comment = "Move {} into {}".format(node.arg1.name, node.lval.name)
                            self.emit_movtoregister_fromstack(reg, node.arg1, comment)
                            if isinstance(node.lval.pascaltype, pascaltypes.SubrangeType):
                                # need to validate that the value is in the range before assigning it
                                self.generate_subrangetest_code(reg, node.lval.pascaltype)
                            # now, get the value from reg into lval.  If lval is a byref parameter, we
                            # need to dereference the pointer.
                            self.emit_movtostack_fromregister(node.lval, reg)
                    elif node.operator == TACOperator.ASSIGNADDRESSOF:
                        assert isinstance(node.lval.pascaltype, pascaltypes.PointerType)
                        comment = "Move address of {} into {}".format(node.arg1.name, node.lval.name)
                        self.emit_movaddresstoregister_fromstack("RAX", node.arg1, comment)
                        self.emit_movtostack_fromregister(node.lval, "RAX")
                    elif node.operator == TACOperator.ASSIGNTODEREF:
                        assert isinstance(node.lval.pascaltype, pascaltypes.PointerType)
                        if isinstance(node.arg1.pascaltype, pascaltypes.ArrayType):
                            assert node.lval.pascaltype.pointstotype.size == node.arg1.pascaltype.size
                            comment = "Copy array {} into {}".format(node.arg1.name, node.lval.name)
                            self.emit_memcopy(node.lval, node.arg1, node.arg1.pascaltype.size, comment, False)
                        else:
                            comment = "Mov {} to address contained in {}".format(node.arg1.name, node.lval.name)
                            # Note - this works with reals just fine, because we will movsd into an xmm register
                            # before doing anything with them.
                            reg = get_register_slice_bybytes("R11", node.arg1.pascaltype.size)
                            self.emit_movtoregister_fromstack(reg, node.arg1, comment)
                            self.emitcode("MOV R10, [{}]".format(node.lval.memoryaddress))
                            self.emitcode("MOV [R10], {}".format(reg))
                    elif node.operator == TACOperator.ASSIGNDEREFTO:
                        assert isinstance(node.arg1.pascaltype, pascaltypes.PointerType)
                        comment = "Mov deref of {} to {}".format(node.arg1.name, node.lval.name)
                        destreg = get_register_slice_bybytes("RAX", node.lval.pascaltype.size)
                        self.emit_movdereftoregister_fromstack(destreg, node.arg1, comment)
                        self.emit_movtostack_fromregister(node.lval, destreg)
                    elif node.operator == TACOperator.NOT:
                        assert isinstance(node.arg1.pascaltype, pascaltypes.BooleanType)
                        assert isinstance(node.lval.pascaltype, pascaltypes.BooleanType)
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
                        litaddress = glt.fetch(node.literal1.value, pascaltypes.StringLiteralType()).memoryaddress
                        comment = "Move literal '{}' into {}".format(node.literal1.value, node.lval.name)
                        self.emitcode("lea rax, [rel {}]".format(litaddress), comment)
                        self.emit_movtostack_fromregister(node.lval, "rax")
                    elif isinstance(node.literal1, RealLiteral):
                        glt = self.tacgenerator.globalliteraltable
                        litaddress = glt.fetch(node.literal1.value, pascaltypes.RealType()).memoryaddress
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
                            tmpreg = get_register_slice_bybytes("RAX", node.lval.pascaltype.size)
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
                            assert isinstance(node.lval.pascaltype, pascaltypes.PointerType)
                            assert isinstance(node.lval.pascaltype.pointstotype, pascaltypes.IntegerType)
                            comment = "Move integer literal {} into address contained in {}"
                            comment = comment.format(node.literal1.value, node.lval.name)
                            self.emitcode("MOV R10, [{}]".format(node.lval.memoryaddress), comment)
                            self.emitcode("MOV [R10], DWORD {}".format(node.literal1.value))

                        else:  # pragma: no cover
                            print(repr(node.operator))
                            assert False

                elif isinstance(node, TACCallFunctionNode) and \
                        not isinstance(node, TACCallSystemFunctionNode):
                    self.generate_procfunc_call_code(block, node, params)

                elif isinstance(node, TACCallSystemFunctionNode):
                    if node.label.name[:6] == "_WRITE":
                        if node.label.name == "_WRITECRLF":
                            outfilesym = params[-1].paramval
                            self.generate_filevariable_statevalidationcode(outfilesym, FILESTATE_GENERATION)
                            assert node.numparams == 1
                            self.emitcode("mov rdi, [{}]".format(outfilesym.memoryaddress))
                            self.emitcode("lea rsi, [rel _printf_newln]")
                            self.emitcode("mov rax, 0")
                            self.emitcode("call fprintf wrt ..plt")
                            self.emitcode("XOR RDI, RDI", "Flush standard output when we do a writeln")
                            self.emitcode("CALL fflush wrt ..plt")
                            self.emitcode("")
                            del params[-1]
                        else:
                            assert node.numparams == 2
                            outfilesym = params[-2].paramval
                            self.generate_filevariable_statevalidationcode(outfilesym, FILESTATE_GENERATION)
                            outparamsym = params[-1].paramval
                            if node.label.name == "_WRITEI":
                                self.emitcode("mov rdi, [{}]".format(outfilesym.memoryaddress))
                                self.emitcode("lea rsi, [rel _printf_intfmt]")
                                destregister = get_register_slice_bybytes("RDX", outparamsym.pascaltype.size)
                                self.emit_movtoregister_fromstackorliteral(destregister, outparamsym)
                                # must pass 0 (in rax) as number of floating point args since fprintf is variadic
                                self.emitcode("mov rax, 0")
                                self.emitcode("call fprintf wrt ..plt")
                            elif node.label.name == "_WRITER":
                                self.emitcode("mov rdi, [{}]".format(outfilesym.memoryaddress))
                                self.emitcode("lea rsi, [rel _printf_realfmt]")
                                self.emit_movtoxmmregister_fromstack("xmm0", outparamsym)
                                self.emitcode("mov rax, 1", "1 floating point param")
                                self.emitcode("call fprintf wrt ..plt")
                            elif node.label.name == "_WRITESL":
                                assert isinstance(outparamsym, ConstantSymbol), type(outparamsym)
                                self.emitcode("mov rdi, [{}]".format(outfilesym.memoryaddress))
                                self.emitcode("mov rsi, [{}]".format(outparamsym.memoryaddress))
                                self.emitcode("mov edx, {}".format(len(outparamsym.value)))
                                self.emitcode("call _PASCAL_PRINTSTRINGTYPE wrt ..plt", "in compiler2_system_io.asm")
                            elif node.label.name == "_WRITEST":
                                assert isinstance(outparamsym, Symbol)
                                assert outparamsym.pascaltype.is_string_type()
                                self.emitcode("mov rdi, [{}]".format(outfilesym.memoryaddress))
                                self.emitcode("mov rsi, [{}]".format(outparamsym.memoryaddress))
                                self.emitcode("mov edx, {}".format(outparamsym.pascaltype.numitemsinarray))
                                self.emitcode("call _PASCAL_PRINTSTRINGTYPE wrt ..plt", "in compiler2_system_io.asm")
                            elif node.label.name == "_WRITEC":
                                self.emit_movtoregister_fromstack("RDI", outparamsym)
                                self.emitcode("mov rsi, [{}]".format(outfilesym.memoryaddress))
                                self.emitcode("call fputc wrt ..plt")
                            elif node.label.name == "_WRITEB":
                                self.emit_movtoregister_fromstack("al", outparamsym)
                                self.emitcode("test al, al")
                                labelfalse = self.getnextlabel()
                                labelprint = self.getnextlabel()
                                self.emitcode("je {}".format(labelfalse))
                                self.emitcode("lea rsi, [rel _printf_true]")
                                self.emitcode("mov edx, 4")
                                self.emitcode("jmp {}".format(labelprint))
                                self.emitlabel(labelfalse)
                                self.emitcode("lea rsi, [rel _printf_false]")
                                self.emitcode("mov edx, 5")
                                self.emitlabel(labelprint)
                                self.emitcode("mov rdi, [{}]".format(outfilesym.memoryaddress))
                                self.emitcode("call _PASCAL_PRINTSTRINGTYPE wrt ..plt", "in compiler2_system_io.asm")
                            del params[-2:]
                    elif node.label.name == "_REWRITE":
                        assert node.numparams == 1
                        outfilesym = params[-1].paramval
                        assert outfilesym.name not in ("input", "output")  # these errors are raised in tac-ir.py

                        # TODO goes away when we add temporary files
                        assert isinstance(outfilesym, ProgramParameterSymbol)

                        # TODO much of these long strings of assembly in this function can be pulled out and this
                        # made easier to manage

                        labelreopen = self.getnextlabel()
                        labeldone = self.getnextlabel()
                        self.emitcode("lea rax, [{}]".format(outfilesym.memoryaddress))
                        self.emitcode("add rax, 8")
                        self.emitcode("mov r11b, byte [rax]", "file state is in r11b")

                        # For FOPEN - RDI gets pointer to filename, RSI gets "w"
                        # For FREOPEN - RDI gets pointer to filename, RSI gets "w", RDX gets the FILE*
                        self.emitcode("mov rdi, [{}]".format(outfilesym.filenamememoryaddress))
                        # TODO gets more complicaed when we can write binary
                        self.emitcode("lea rsi, [rel _filemode_write]")
                        self.emitcode("test r11b, r11b", "determine if we need to open or reopen this file")
                        self.emitcode("jg {}".format(labelreopen))
                        self.emitcode("call fopen wrt ..plt", "FILE* is in RAX")
                        self.emitcode("jmp {}".format(labeldone))
                        self.emitlabel(labelreopen)
                        self.emitcode("mov rdx, [{}]".format(outfilesym.memoryaddress))
                        self.emitcode("call freopen wrt ..plt", "FILE* is in RAX")
                        self.emitlabel(labeldone)
                        self.emitcode("test rax, rax")
                        self.emit_jumptoerror("jz", "_PASCAL_FOPEN_ERROR")
                        self.emitcode("lea r11, [{}]".format(outfilesym.memoryaddress))
                        self.emitcode("mov [r11], rax")
                        self.emitcode("add r11, 8")
                        self.emitcode("mov [r11], byte {}".format(FILESTATE_GENERATION))
                        del params[-1]
                    elif node.label.name == "_SQRTR":
                        comment = "parameter {} for sqrt()".format(str(params[-1].paramval))
                        self.emit_movtoxmmregister_fromstack("xmm0", params[-1].paramval, comment)
                        self.emitcode("xorps xmm8, xmm8", "validate parameter is >= 0")
                        self.emitcode("ucomisd xmm0, xmm8")
                        self.emit_jumptoerror("jb", "_PASCAL_SQRT_ERROR")
                        self.emitcode("sqrtsd xmm0, xmm0", 'sqrt()')
                        comment = "assign return value of function to {}".format(node.lval.name)
                        # Currently all the system functions use a temporary, which I know is not byref.
                        # So, technically it would be quicker to do this:
                        # self.emitcode("MOVSD [{}], XMM0".format(node.lval.memoryaddress), comment)
                        # however, to future-proof this for optimizations, I'll use the movtostack() functions
                        self.emit_movtostack_fromxmmregister(node.lval, "XMM0", comment)
                    elif node.label.name in ("_SINR", "_COSR"):
                        self.used_x87_code = True
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
                    elif node.label.name == "_ARCTANR":
                        self.used_x87_code = True
                        comment = "parameter {} for arctan()".format(str(params[-1].paramval))
                        self.emit_movtoxmmregister_fromstack("xmm0", params[-1].paramval, comment)
                        # sin() and cos() use the legacy x87 FPU.  This is slow but also very few instructions
                        # so easy for the compiler writer.  In x86-64 one is supposed to use library functions
                        # for this, but this is faster to code.
                        # Cannot move directly from xmm0 to the FPU stack; cannot move directly from a standard
                        # register to the FPU stack.  Can only move from memory
                        self.emitcode("movsd [{}], xmm0".format(node.lval.memoryaddress),
                                      "use {} to move value to FPU".format(node.lval.name))
                        self.emitcode("fld qword [{}]".format(node.lval.memoryaddress))
                        # Pascal uses atan but x87 uses atan2.
                        self.emitcode("fld1")
                        self.emitcode("fpatan")
                        comment = "assign return value of function to {}".format(node.lval.name)
                        # TODO - see comment to _SQRTR where I use the movtostack() functions.  Technically
                        # there should be a test for node.lval.is_byref here, but for now I know it has to be
                        # a local temporary, not a byref parameter, so this is safe.  I don't want to write
                        # a fstp equivalent for that function when I don't need it.
                        self.emitcode("fstp qword [{}]".format(node.lval.memoryaddress), comment)
                    elif node.label.name == '_LNR':
                        self.used_x87_code = True
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
                        self.emit_jumptoerror("jbe", "_PASCAL_LN_ERROR")
                        self.emitcode("FLDLN2")
                        self.emitcode("FLD QWORD [{}]".format(node.lval.memoryaddress))
                        self.emitcode("FYL2X")
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emitcode("fstp qword [{}]".format(node.lval.memoryaddress), comment)
                    elif node.label.name == '_EXPR':
                        self.used_x87_code = True
                        comment = "parameter {} for exp()".format(str(params[-1].paramval))
                        self.emit_movtoxmmregister_fromstack("xmm0", params[-1].paramval, comment)
                        # The code that I got from https://stackoverflow.com/questions/44957136
                        # and http://www.ray.masmcode.com/tutorial/fpuchap11.htm worked in many cases but not all.
                        # Used ChatGPT to assist.

                        self.emitcode("movsd [{}], xmm0".format(node.lval.memoryaddress),
                                      "use {} to move value to FPU".format(node.lval.name))
                        self.emitcode("FLD QWORD [{}]".format(node.lval.memoryaddress))

                        # compute y = x * log2(e)
                        self.emitcode("FLDL2E")  # ST0 = log2(e), ST1 = x
                        self.emitcode("FMULP ST1, ST0")  # ST0 = x * log2(e) = y

                        # split y into integer n and fractional f
                        self.emitcode("FLD ST0")  # ST0 = y, ST1 = y
                        self.emitcode("FRNDINT")  # ST0 = n (rounded y), ST1 = y
                        self.emitcode("FSUB ST1, ST0")  # ST1 = y-n = f, ST0 = n
                        self.emitcode("FXCH ST1")  # ST0 = y-n = f, ST1 = n

                        # compute 2^f using f2xm1
                        self.emitcode("F2XM1")  # ST0 = 2^f - 1, ST1 = n
                        self.emitcode("FLD1")  # ST0 = 1, ST1 = 2^f - 1, ST2 = n
                        self.emitcode("FADDP ST1, ST0")  # ST0 = 2^f, ST1 = n

                        # scale by 2^n: result = 2^(n+f) = e^x
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
                        self.emit_jumptoerror("jo", "_PASCAL_OVERFLOW_ERROR")
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emit_movtostack_fromregister(node.lval, "EAX", comment)
                    elif node.label.name == "_CHRI":
                        comment = "parameter {} for chr()".format(str(params[-1].paramval))
                        self.emit_movtoregister_fromstackorliteral("R11D", params[-1].paramval, comment)
                        self.emitcode("CMP R11D, 0")
                        self.emit_jumptoerror("JL", "_PASCAL_CHR_ERROR")
                        self.emitcode("CMP R11D, 255")
                        self.emit_jumptoerror("JG", "_PASCAL_CHR_ERROR")
                        self.emitcode("MOV AL, R11B", "take least significant 8 bits")
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emit_movtostack_fromregister(node.lval, "AL", comment)
                    elif node.label.name == "_ORDO":
                        # Returns the integer representation of the ordinal type.  Since under the covers,
                        # ordinal types are stored as integers, this is just returning itself.
                        # Trick is that the ordinal type may be 1 byte (boolean, character, or user-defined ordinal)
                        # or 4 bytes (integer).  If it's one byte, we need to zero-extend it.
                        assert params[-1].paramval.pascaltype.size in (1, 4)

                        comment = "parameter {} for ord()".format(str(params[-1].paramval))
                        if params[-1].paramval.pascaltype.size == 1:
                            # TODO - this can easily be done in a single mov statement of the form
                            # movzx EAX, byte [rbp-8]
                            # or whatever - but need to decide whether it's worth hacking up
                            # emit_movtoregister_fromstack to handle this one-off.
                            self.emit_movtoregister_fromstack("R11B", params[-1].paramval, comment)
                            self.emitcode("MOVZX EAX, R11B")
                        else:
                            self.emit_movtoregister_fromstackorliteral("EAX", params[-1].paramval)
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emit_movtostack_fromregister(node.lval, "EAX", comment)
                    elif node.label.name == "_SUCCO":
                        assert params[-1].paramval.pascaltype.size in (1, 4)
                        assert node.lval.pascaltype.size == params[-1].paramval.pascaltype.size
                        comment = "parameter {} for succ()".format(str(params[-1].paramval))
                        reg = get_register_slice_bybytes("RAX", node.lval.pascaltype.size)
                        bt = params[-1].paramval.pascaltype

                        self.emit_movtoregister_fromstackorliteral(reg, params[-1].paramval, comment)

                        if isinstance(bt, pascaltypes.CharacterType):
                            self.emitcode("CMP {}, 255".format(reg))
                            self.emit_jumptoerror("JE", "_PASCAL_SUCC_PRED_ERROR")  # cannot increment a char past 255

                        self.emitcode("INC {}".format(reg))

                        if isinstance(bt, pascaltypes.IntegerType):
                            self.emit_jumptoerror("jo", "_PASCAL_SUCC_PRED_ERROR")
                        elif isinstance(bt, pascaltypes.BooleanType):
                            self.emitcode("CMP {}, 1".format(reg))
                            self.emit_jumptoerror("JG", "_PASCAL_SUCC_PRED_ERROR")
                        elif isinstance(bt, pascaltypes.SubrangeType):
                            self.generate_subrangetest_code(reg, bt)
                        elif isinstance(bt, pascaltypes.CharacterType):
                            pass  # did the test for overflow above.
                        else:
                            assert isinstance(bt, pascaltypes.EnumeratedType)
                            self.emitcode("CMP {}, {}".format(reg, str(len(bt.value_list))))
                            self.emit_jumptoerror("JGE", "_PASCAL_SUCC_PRED_ERROR")
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emit_movtostack_fromregister(node.lval, reg, comment)
                    elif node.label.name == "_PREDO":
                        assert params[-1].paramval.pascaltype.size in (1, 4)
                        assert node.lval.pascaltype.size == params[-1].paramval.pascaltype.size
                        comment = "parameter {} for pred()".format(str(params[-1].paramval))
                        reg = get_register_slice_bybytes("RAX", node.lval.pascaltype.size)

                        self.emit_movtoregister_fromstackorliteral(reg, params[-1].paramval, comment)
                        self.emitcode("DEC {}".format(reg))
                        bt = params[-1].paramval.pascaltype
                        if isinstance(bt, pascaltypes.IntegerType):
                            self.emit_jumptoerror("jo", "_PASCAL_SUCC_PRED_ERROR")
                        elif isinstance(bt, pascaltypes.SubrangeType):
                            self.generate_subrangetest_code(reg, bt)
                        else:
                            self.emitcode("CMP {}, 0".format(reg))
                            self.emit_jumptoerror("JL", "_PASCAL_SUCC_PRED_ERROR")
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emit_movtostack_fromregister(node.lval, reg, comment)
                    elif node.label.name in ("_ROUNDR", "_TRUNCR"):
                        comment = "parameter {} for {}()".format(str(params[-1].paramval), node.label.name[1:6].lower())
                        self.emit_movtoxmmregister_fromstack("xmm0", params[-1].paramval, comment)
                        assert node.lval.pascaltype.size in (4, 8)  # can't round into 1 or 2 bytes
                        destreg = get_register_slice_bybytes("RAX", node.lval.pascaltype.size)
                        if node.label.name == "_ROUNDR":
                            instruction = "CVTSD2SI"
                        else:
                            instruction = "CVTTSD2SI"
                        # TODO - test for overflow here
                        self.emitcode("{} {}, XMM0".format(instruction, destreg))
                        comment = "assign return value of function to {}".format(node.lval.name)
                        self.emit_movtostack_fromregister(node.lval, destreg, comment)
                    else:  # pragma: no cover
                        raise ASMGeneratorError(compiler_failstr("Invalid System Function: {}".format(node.label.name)))
                elif isinstance(node, TACBinaryNodeWithBoundsCheck):
                    # currently only used for math with structured types where we have pointers
                    assert isinstance(node.result.pascaltype, pascaltypes.PointerType)
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
                        self.emit_jumptoerror("JL", "_PASCAL_ARRAYINDEX_ERROR")

                        # we are only adding to pointers that point to arrays.  Not adding to pointers in the middle
                        # of arrays.  And the addition is always a multiple of the size of the component type.
                        # So, if the number of bytes being added is greater than the size allocated to the pointer,
                        # we have gone over and this would be an index error

                        # TODO - assert someplace that when we're adding we're adding the right multiple.
                        self.emitcode("CMP R11D, {}".format(str(node.upperbound)))
                        self.emit_jumptoerror("JG", "_PASCAL_ARRAYINDEX_ERROR")

                    self.emitcode("add rax, r11")
                    self.emit_jumptoerror("jo", "_PASCAL_OVERFLOW_ERROR")
                    self.emit_movtostack_fromregister(node.result, "rax")

                elif isinstance(node, TACBinaryNode):

                    assert isinstance(node.result.pascaltype, pascaltypes.IntegerType) or \
                           isinstance(node.result.pascaltype, pascaltypes.BooleanType) or \
                           isinstance(node.result.pascaltype, pascaltypes.RealType)

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

                            self.emit_movtoregister_fromstackorliteral("eax", node.arg1, comment)
                            self.emit_movtoregister_fromstackorliteral("r11d", node.arg2)
                            self.emitcode("{} eax, r11d".format(op))
                            self.emit_jumptoerror("jo", "_PASCAL_OVERFLOW_ERROR")
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
                                self.emit_jumptoerror("je", "_PASCAL_DIVZERO_ERROR")
                            else:
                                self.emit_jumptoerror("jle", "_PASCAL_MOD_ERROR")
                            self.emitcode("cdq", "sign extend eax -> edx:eax")
                            self.emitcode("idiv r11d")
                            if node.operator == TACOperator.MOD:
                                self.emitcode("MOV EAX, EDX", "Remainder of IDIV is in EDX")
                                posmodlabel = self.getnextlabel()
                                self.emitcode("CMP EAX, 0")
                                self.emitcode("JGE {}".format(posmodlabel))
                                self.emitcode("ADD EAX, R11D")
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

                    else:
                        assert isinstance(node.result.pascaltype, pascaltypes.BooleanType)
                        n1type = node.arg1.pascaltype
                        n2type = node.arg2.pascaltype

                        assert block.symboltable.are_compatible(n1type.identifier, n2type.identifier, node.arg1,
                                                                node.arg2)

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
                            if n1type.is_string_type() or isinstance(n1type, pascaltypes.StringLiteralType):
                                self.emitcode("MOV RDI, [{}]".format(node.arg1.memoryaddress), comment)
                                self.emitcode("MOV RSI, [{}]".format(node.arg2.memoryaddress))
                                if n1type.is_string_type():
                                    length = n1type.numitemsinarray
                                else:
                                    assert isinstance(node.arg1, ConstantSymbol)
                                    length = len(node.arg1.value)
                                self.emitcode("MOV EDX, {}".format(str(length)))
                                self.emitcode("CALL _PASCAL_STRINGCOMPARE")
                                self.emitcode("TEST AL, AL")
                            elif isinstance(n1type, pascaltypes.IntegerType) or \
                                    (isinstance(n1type, pascaltypes.SubrangeType) and
                                     n1type.hosttype.size == 4):
                                self.emit_movtoregister_fromstackorliteral("eax", node.arg1, comment)
                                self.emit_movtoregister_fromstackorliteral("r11d", node.arg2)
                                self.emitcode("cmp eax, r11d")
                            elif isinstance(n1type, pascaltypes.BooleanType) or \
                                    isinstance(n1type, pascaltypes.CharacterType) or \
                                    isinstance(n1type, pascaltypes.EnumeratedType) or \
                                    (isinstance(n1type, pascaltypes.SubrangeType) and
                                     n1type.hosttype.size == 1):
                                self.emit_movtoregister_fromstack("al", node.arg1, comment)
                                self.emit_movtoregister_fromstack("r11b", node.arg2)
                                self.emitcode("cmp al, r11b")
                            else:  # has to be real; we errored above if any other type
                                assert isinstance(n1type, pascaltypes.RealType)
                                self.emit_movtoxmmregister_fromstack("xmm0", node.arg1)
                                self.emit_movtoxmmregister_fromstack("xmm8", node.arg2)
                                self.emitcode("ucomisd xmm0, xmm8")

                            if isinstance(n1type, pascaltypes.BooleanType) or \
                                    isinstance(n1type, pascaltypes.IntegerType) or \
                                    is_integerorboolean_subrangetype(n1type) or \
                                    n1type.is_string_type() or \
                                    isinstance(n1type, pascaltypes.StringLiteralType):

                                # Boolean and Integer share same jump instructions, and strings
                                # are set up to do an integer comparison by this point
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

            if block.ismain:
                # deallocate global arrays
                # TODO: refactor this loop to be something like "get global array symbols" or something
                for symname in self.tacgenerator.globalsymboltable.symbols.keys():
                    sym = self.tacgenerator.globalsymboltable.fetch(symname)
                    if isinstance(sym, Symbol) and isinstance(sym.pascaltype, pascaltypes.ArrayType):
                        self.emitcode("mov rdi, [{}]".format(sym.memoryaddress),
                                      "Free memory for global array {}".format(symname))
                        self.used_dispose = True
                        self.emitcode("call _PASCAL_DISPOSE_MEMORY")
            else:
                # deallocate local arrays
                for symname in block.symboltable.symbols.keys():
                    if block.paramlist.fetch(symname) is None:
                        localsym = block.symboltable.symbols[symname]
                        if isinstance(localsym, Symbol) and not isinstance(localsym, FunctionResultVariableSymbol):
                            if isinstance(localsym.pascaltype, pascaltypes.ArrayType):
                                self.emitcode("mov rdi, [{}]".format(localsym.memoryaddress),
                                              "Free memory for local array {}".format(symname))
                                self.used_dispose = True
                                self.emitcode("call _PASCAL_DISPOSE_MEMORY")

            if totalstorageneeded > 0 or block.ismain:
                self.emitcode("MOV RSP, RBP", "restore stack pointer")
                self.emitcode("POP RBP")

            if not block.ismain:
                self.emitcode("RET")

    def generate_helperfunctioncode(self):
        if self.used_calloc:
            self.emitlabel("_PASCAL_ALLOCATE_MEMORY")
            self.emitcomment("takes a number of members (RDI) and a size (RSI)")
            self.emitcomment("returns pointer to memory in RAX.")
            # just a passthrough for CALLOC
            # yes, calloc() initializes memory and Pascal is not supposed to do so, but calloc() is safer
            # in that it tests for an overflow when you multiply nmemb * size whereas malloc() does not.
            self.emitcode("call calloc wrt ..plt")
            self.emitcode("test rax, rax")
            self.emit_jumptoerror("jle", "_PASCAL_CALLOC_ERROR")
            self.emitcode("ret")
        if self.used_dispose:
            self.emitlabel("_PASCAL_DISPOSE_MEMORY")
            self.emitcomment("takes a pointer to memory (RDI)")
            # just a passthrough for FREE
            self.emitcode("call free wrt ..plt")
            self.emitcode("test rax, rax")
            self.emit_jumptoerror("jl", "_PASCAL_DISPOSE_ERROR")
            self.emitcode("ret")

    def generate_errorhandlingcode(self):
        for i in self.pascalerrors.keys():
            if self.pascalerrors[i].isused:
                self.emitlabel(self.pascalerrors[i].label)
                self.emitcode("lea rsi, [rel _pascalerr_{}]".format(str(i)))
                self.emitcode("mov rdx, {}".format(len(self.pascalerrors[i].errorstr)))
                self.emitcode("jmp _PASCAL_PRINT_ERROR")

        self.emitlabel("_PASCAL_PRINT_ERROR")
        self.emitcomment("required: pointer to error message in rsi, length of message in rdx")
        self.emitcode("PUSH RSI")
        self.emitcode("PUSH RDX")  # we pushed 16-bytes so stack is still 16-byte aligned
        self.emitcode("XOR RDI, RDI", "need to flush any buffered output before printing the error")
        self.emitcode("CALL fflush wrt ..plt")
        self.emitcode("POP RDX")
        self.emitcode("POP RSI")
        # uses syscalls here because we don't know if "output" was defined
        self.emitcode("mov rax, 1")
        self.emitcode("mov rdi, 1", "1 = stdout")
        self.emitcode("syscall")
        self.emitcode("jmp _PASCAL_EXIT")

    def generate_programterminationcode(self):
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
        self.generate_programterminationcode()

    def generate_gnu_stack_section(self):
        # notify the linker that we do not need an executable stack
        self.emitsection("note.GNU-stack noalloc noexec nowrite progbits")

    def generate_bsssection(self):
        if len(self.tacgenerator.globalsymboltable.symbols.keys()) > 0:
            self.emitsection("bss")
            varseq = 0
            for symname in self.tacgenerator.globalsymboltable.symbols.keys():
                sym = self.tacgenerator.globalsymboltable.fetch(symname)
                if isinstance(sym, Symbol) and not isinstance(sym, ActivationSymbol):
                    if isinstance(sym, ProgramParameterSymbol):
                        if sym.name not in ("input", "output"):
                            label2 = "_globalvar_{}_filenameptr".format(sym.name)
                            sym.filenamememoryaddress = "rel {}".format(label2)
                            self.emitcode("{} resb {}".format(label2, 8), "holds pointer to command-line arg")
                        label = "_globalvar_{}".format(sym.name)
                    else:
                        label = "_globalvar_{}".format(str(varseq))
                        varseq += 1
                    sym.memoryaddress = "rel {}".format(label)
                    if isinstance(sym.pascaltype, pascaltypes.ArrayType):
                        self.emitcode("{} resb 8".format(label),
                                      "address for global array variable {}".format(symname))
                    else:
                        self.emitcode("{} resb {}".format(label, sym.pascaltype.size),
                                      "global variable {}".format(symname))

    def generate(self, objfilename, exefilename):
        self.generate_externs()
        self.generate_gnu_stack_section()
        self.generate_bsssection()
        self.generate_datasection()
        self.generate_textsection()
        self.asmfile.close()
        os.system("nasm -f elf64 -F dwarf -g -o compiler2_system_io.o compiler2_system_io.asm")
        os.system("nasm -f elf64 -F dwarf -g -o compiler2_stringcompare.o compiler2_stringcompare.asm")
        os.system("nasm -f elf64 -F dwarf -g -o {} {}".format(objfilename, self.asmfilename))
        os.system("gcc {} -o {} compiler2_system_io.o compiler2_stringcompare.o".format(objfilename, exefilename))
