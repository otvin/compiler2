import os
from tac_ir import TACBlock, TACLabelNode, TACParamNode, TACCallSystemFunctionNode, TACUnaryLiteralNode, \
    TACOperator, TACGenerator, TACCommentNode, TACBinaryNode, TACUnaryNode
from symboltable import StringLiteral, NumericLiteral, Symbol
import pascaltypes


class ASMGeneratorError(Exception):
    pass


# TODO - https://stackoverflow.com/questions/41573502/why-doesnt-gcc-use-partial-registers - when we get to types that
# are 1 or 2 bytes, need to make sure we don't get in trouble.

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
            self.emitln('\t' + s + '\t\t;' + comment)

    def emitlabel(self, labelname):
        self.emitln(labelname + ":")

    def emitsection(self, sectionname):
        self.emitln("section .{}".format(sectionname))

    def emitcomment(self, commentstr):
        self.emitln("; {}".format(commentstr))

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
                else:
                    raise ASMGeneratorError("Invalid literal type")

    def generate_code(self):
        params = []  # this is a stack of parameters

        for block in self.tacgenerator.tacblocks:
            assert isinstance(block, TACBlock)
            self.emitlabel(block.label.name)

            # align stack pointer
            # todo - make main an attribute of the block instead of testing for label name
            if block.label.name == 'main':
                self.emitcode("AND RSP, -16")

            # TODO - if this is a procedure or function block we need to allocate temp space for parameters
            # pass #1 - compute local storage needs

            totalstorageneeded = 0  # measured in bytes

            for symname in block.symboltable.symbols.keys():
                sym = block.symboltable.fetch(symname)
                assert isinstance(sym, Symbol)
                if sym.memoryaddress is None:
                    totalstorageneeded += sym.pascaltype.size
                    sym.memoryaddress = "RBP-{}".format(str(totalstorageneeded))

            if totalstorageneeded > 0:
                self.emitcode("PUSH RBP")  # ABI requires callee to preserve RBP
                self.emitcode("MOV RBP, RSP", "save stack pointer")
                # X86-64 ABI requires stack to stay aligned to 16-byte boundary.  Make sure we subtract in chunks of 16.
                totalstorageneeded += 16 - (totalstorageneeded % 16)
                self.emitcode("SUB RSP, " + str(totalstorageneeded), "allocate local storage")

            for node in block.tacnodes:
                if isinstance(node, TACCommentNode):
                    self.emitcomment(node.comment)
                elif isinstance(node, TACLabelNode):
                    self.emitlabel(node.label.name)
                elif isinstance(node, TACParamNode):
                    params.append(node)
                elif isinstance(node, TACUnaryNode):
                    if node.operator == TACOperator.INTTOREAL:
                        if node.arg1.pascaltype.size in (1, 2):
                            raise ASMGeneratorError("Cannot handle 8- or 16-bit int convert to real")
                        elif node.arg1.pascaltype.size == 4:
                            # extend to 8 bytes
                            self.emitcode("mov eax, [{}]".format(node.arg1.memoryaddress))
                            self.emitcode("cdqe")
                        elif node.arg1.pascaltype.size == 8:
                            self.emitcode("mov rax, [{}]".format(node.arg1.memoryaddress))
                        else:
                            raise ASMGeneratorError("Invalid size for integer")
                        # rax now has the value we need to convert to the float
                        self.emitcode("cvtsi2sd xmm0, rax")
                        # now save the float into its location
                        self.emitcode("movsd [{}], xmm0".format(node.lval.memoryaddress))
                    elif node.operator == TACOperator.ASSIGN:
                        if node.lval.pascaltype.size == 1:
                            reg = "al"
                        elif node.lval.pascaltype.size == 2:
                            reg = "ax"
                        elif node.lval.pascaltype.size == 4:
                            reg = "eax"
                        elif node.lval.pascaltype.size == 8:
                            reg = "rax"
                        else:
                            raise ASMGeneratorError("Invalid Size for assignment")
                        # This may be overkill - but at this point I don't know if I will be using rax for anything
                        # else, so it's safest to preserve since I'm inside a block of code.
                        self.emitcode("push rax")
                        self.emitcode("mov {}, [{}]".format(reg, node.arg1.memoryaddress))
                        self.emitcode("mov [{}], {}".format(node.lval.memoryaddress, reg))
                        self.emitcode("pop rax")
                    else:
                        raise ASMGeneratorError("Invalid operator: {}".format(node.operator))
                elif isinstance(node, TACUnaryLiteralNode):
                    if isinstance(node.literal1, StringLiteral):
                        # dealing with PEP8 line length
                        glt = self.tacgenerator.globalliteraltable
                        litaddress = glt.fetch(node.literal1.value, pascaltypes.StringLiteralType()).memoryaddress
                        self.emitcode("lea rax, [rel {}]".format(litaddress))
                        self.emitcode("mov [{}], rax".format(node.lval.memoryaddress))
                    elif isinstance(node.literal1, NumericLiteral) and isinstance(node.literal1.pascaltype,
                                                                                  pascaltypes.RealType):
                        glt = self.tacgenerator.globalliteraltable
                        litaddress = glt.fetch(node.literal1.value, pascaltypes.RealType()).memoryaddress
                        self.emitcode("movsd xmm0, [rel {}]".format(litaddress))
                        self.emitcode("movsd [{}], xmm0".format(node.lval.memoryaddress))
                    else:
                        # TODO is node.operator ever anything other than ASSIGN?
                        if node.operator == TACOperator.ASSIGN:
                            if node.lval.pascaltype.size == 1:
                                sizedirective = "BYTE"
                            elif node.lval.pascaltype.size == 2:
                                sizedirective = "WORD"
                            elif node.lval.pascaltype.size == 4:
                                sizedirective = "DWORD"
                            elif node.lval.pascaltype.size == 8:
                                sizedirective = "QWORD"
                            else:
                                raise ASMGeneratorError("Invalid Size for assignment")
                            self.emitcode("mov [{}], {} {}".format(node.lval.memoryaddress, sizedirective,
                                                                   node.literal1.value))
                elif isinstance(node, TACCallSystemFunctionNode):
                    if node.label.name == "_WRITEI":
                        if node.numparams != 1:
                            raise ASMGeneratorError("Invalid numparams to _WRITEI")
                        self.emitcode("push rdi")
                        self.emitcode("push rsi")
                        self.emitcode("mov rdi, _printf_intfmt")
                        if params[0].paramval.pascaltype.size == 1:
                            destregister = "sil"
                        elif params[0].paramval.pascaltype.size == 2:
                            destregister = "si"
                        elif params[0].paramval.pascaltype.size == 4:
                            destregister = "esi"
                        elif params[0].paramval.pascaltype.size == 8:
                            destregister = "rsi"
                        else:
                            raise ASMGeneratorError("Invalid Size for _WRITEI")
                        self.emitcode("mov {}, [{}]".format(destregister, params[0].paramval.memoryaddress))
                        # must pass 0 (in rax) as number of floating point args since printf is variadic
                        self.emitcode("mov rax, 0")
                        self.emitcode("call printf wrt ..plt")
                        self.emitcode("pop rsi")
                        self.emitcode("pop rdi")
                        del params[-1]
                    elif node.label.name == "_WRITER":
                        if node.numparams != 1:
                            raise ASMGeneratorError("Invalid numparams to _WRITER")
                        self.emitcode("push rdi")
                        self.emitcode("mov rdi, _printf_realfmt")
                        self.emitcode("movsd xmm0, [{}]".format(params[0].paramval.memoryaddress))
                        self.emitcode("mov rax, 1", "1 floating point param")
                        self.emitcode("call printf wrt ..plt")
                        self.emitcode("pop rdi")
                        del params[-1]
                    elif node.label.name == "_WRITES":
                        self.emitcode("push rdi")
                        self.emitcode("push rsi")
                        self.emitcode("mov rdi, _printf_strfmt")
                        self.emitcode("mov rsi, [{}]".format(params[0].paramval.memoryaddress))
                        self.emitcode("mov rax, 0")
                        self.emitcode("call printf wrt ..plt")
                        self.emitcode("pop rsi")
                        self.emitcode("pop rdi")
                        del params[-1]
                    elif node.label.name == "_WRITEB":
                        self.emitcode("push rdi")
                        self.emitcode("push rsi")
                        self.emitcode("mov rdi, _printf_strfmt")
                        self.emitcode("mov al, [{}]".format(params[0].paramval.memoryaddress))
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
                        self.emitcode("pop rsi")
                        self.emitcode("pop rdi")
                        del params[-1]
                    elif node.label.name == "_WRITECRLF":
                        self.emitcode("push rdi")
                        self.emitcode("mov rdi, _printf_newln")
                        self.emitcode("mov rax, 0")
                        self.emitcode("call printf wrt ..plt")
                        self.emitcomment("Flush standard output when we do a writeln")
                        self.emitcode("XOR RDI, RDI")
                        self.emitcode("CALL fflush wrt ..plt")
                        self.emitcode("pop rdi")
                        self.emitcode("")
                    else:
                        raise ASMGeneratorError("Invalid System Function: {}".format(node.label.name))
                elif isinstance(node, TACBinaryNode):
                    if isinstance(node.result.pascaltype, pascaltypes.IntegerType):
                        # TODO - handle something other than 4-byte integers
                        if node.operator in (TACOperator.MULTIPLY, TACOperator.ADD, TACOperator.SUBTRACT):
                            if node.operator == TACOperator.MULTIPLY:
                                op = "imul"
                            elif node.operator == TACOperator.ADD:
                                op = "add"
                            else:
                                op = "sub"
                            self.emitcode("mov eax, [{}]".format(node.arg1.memoryaddress))
                            self.emitcode("mov r11d, [{}]".format(node.arg2.memoryaddress))
                            self.emitcode("{} eax, r11d".format(op))
                            self.emitcode("jo _PASCAL_OVERFLOW_ERROR")
                            self.emitcode("mov [{}], eax".format(node.result.memoryaddress))
                        elif node.operator in (TACOperator.IDIV, TACOperator.MOD):
                            self.emitcode("mov eax, [{}]".format(node.arg1.memoryaddress))
                            self.emitcode("mov r11d, [{}]".format(node.arg2.memoryaddress))
                            # Error D.45: 6.7.2.2 of ISO Standard requires testing for division by zero at runtime
                            # Error D.46: 6.7.2.2 also says it is an error if the second term is not positive
                            self.emitcode("test r11d, r11d", "check for division by zero")
                            if node.operator == TACOperator.IDIV:
                                self.emitcode("je _PASCAL_DIVZERO_ERROR")
                            else:
                                self.emitcode("jle _PASCAL_MOD_ERROR")
                            self.emitcode("cdq", "sign extend eax -> edx:eax")
                            self.emitcode("idiv r11d")
                            if node.operator == TACOperator.MOD:
                                self.emitcode("MOV EAX, EDX", "Remainder of IDIV is in EDX")
                            self.emitcode("mov [{}], eax".format(node.result.memoryaddress))
                        else:
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
                        else:
                            raise ASMGeneratorError("Unrecognized operator: {}".format(node.operator))
                        self.emitcode("movsd xmm0, [{}]".format(node.arg1.memoryaddress))
                        self.emitcode("movsd xmm8, [{}]".format(node.arg2.memoryaddress))
                        self.emitcode("{} xmm0, xmm8".format(op))
                        self.emitcode("movsd [{}], xmm0".format(node.result.memoryaddress))
                    else:
                        raise ASMGeneratorError("Invalid Type {}".format(node.result.pascaltype))
                else:
                    raise Exception("Some better exception")

            if totalstorageneeded > 0:
                self.emitcode("POP RBP")

    def generate_errorhandlingcode(self):
        # overflow
        self.emitcomment("overflow error")
        self.emitlabel("_PASCAL_OVERFLOW_ERROR")
        self.emitcode("push rdi")
        self.emitcode("mov rdi, _stringerr_0")
        self.emitcode("jmp _PASCAL_PRINT_ERROR")
        self.emitlabel("_PASCAL_DIVZERO_ERROR")
        self.emitcode("push rdi")
        self.emitcode("mov rdi, _stringerr_1")
        self.emitcode("jmp _PASCAL_PRINT_ERROR")
        self.emitlabel("_PASCAL_MOD_ERROR")
        self.emitcode("push rdi")
        self.emitcode("mov rdi, _stringerr_2")
        self.emitcode("jmp _PASCAL_PRINT_ERROR")

        self.emitlabel("_PASCAL_PRINT_ERROR")
        self.emitcomment("required: pointer to error message in rdi")
        self.emitcode("mov rax, 0")
        self.emitcode("call printf wrt ..plt")
        self.emitcode("pop rdi")
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
