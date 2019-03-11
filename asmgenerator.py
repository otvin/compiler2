import os
from tac_ir import TACBlock, TACLabelNode, TACParamNode, TACCallSystemFunctionNode, TACUnaryLiteralNode, \
    TACOperator, TACGenerator, TACCommentNode, TACBinaryNode
from symboltable import StringLiteral, NumericLiteral
import pascaltypes


class ASMGeneratorError(Exception):
    pass


class AssemblyGenerator:
    def __init__(self, asmfilename, tacgenerator):
        assert isinstance(tacgenerator, TACGenerator)
        self.asmfilename = asmfilename
        self.asmfile = open(asmfilename, 'w')
        self.tacgenerator = tacgenerator

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

    def generate_externs(self):
        self.emitcode("extern printf")
        self.emitcode("extern fflush")
        self.emitcode("extern prtdbl", "imported from nsm64")

    def generate_datasection(self):
        self.emitsection("data")
        self.emitcomment("error handling strings")
        self.emitcode('stringerr_0 db `Overflow error`, 0')
        self.emitcomment("support for write() commands")
        self.emitcode('printf_intfmt db "%d",0')
        self.emitcode('printf_strfmt db "%s",0')
        self.emitcode('printf_realfmt db "%f",0')
        self.emitcode('printf_newln db 10,0')
        if len(self.tacgenerator.globalliteraltable) > 0:
            nextid = 0
            for lit in self.tacgenerator.globalliteraltable:
                if isinstance(lit, StringLiteral):
                    litname = 'stringlit_{}'.format(nextid)
                    nextid += 1
                    if len(lit.value) > 255:
                        raise ASMGeneratorError("String literal {} exceeds 255 char max length.".format(lit.value))
                    self.emitcode("{} db `{}`, 0".format(litname, lit.value.replace('`', '\\`')))
                    lit.setaddress(litname)
                elif isinstance(lit, NumericLiteral) and isinstance(lit.pascaltype, pascaltypes.RealType):
                    litname = 'reallit_{}'.format(nextid)
                    nextid += 1
                    self.emitcode("{} dq {}".format(litname, lit.value))
                    lit.setaddress(litname)
                else:
                    raise ASMGeneratorError("Invalid literal type")

    def generate_code(self):
        params = []  # this is a stack of parameters

        for block in self.tacgenerator.tacblocks:
            assert isinstance(block, TACBlock)
            self.emitlabel(block.label.name)

            # TODO - if this is a procedure or function block we need to allocate temp space for parameters
            # pass #1 - compute local storage needs

            totalstorageneeded = 0  # measured in bytes
            for node in block.tacnodes:
                if isinstance(node, TACUnaryLiteralNode):
                    # TODO - another spot where the operator may always be assign
                    if node.operator == TACOperator.ASSIGN:
                        if isinstance(node.literal1, StringLiteral):
                            totalstorageneeded += 8
                        else:
                            totalstorageneeded += node.lval.pascaltype.size
                        node.lval.setaddress("RBP-{}".format(str(totalstorageneeded)))
                elif isinstance(node, TACBinaryNode):
                    totalstorageneeded += node.result.pascaltype.size
                    node.result.setaddress("RBP-{}".format(str(totalstorageneeded)))

            if totalstorageneeded > 0:
                self.emitcode("PUSH RBP")  # ABI requires callee to preserve RBP
                self.emitcode("MOV RBP, RSP", "save stack pointer")
                self.emitcode("SUB RSP, " + str(totalstorageneeded), "allocate local storage")

            for node in block.tacnodes:
                if isinstance(node, TACCommentNode):
                    self.emitcomment(node.comment)
                elif isinstance(node, TACLabelNode):
                    self.emitlabel(node.label.name)
                elif isinstance(node, TACParamNode):
                    params.append(node)
                elif isinstance(node, TACUnaryLiteralNode):
                    if isinstance(node.literal1, StringLiteral):
                        litaddress = self.tacgenerator.globalliteraltable.fetch(str(node.literal1.value)).memoryaddress
                        self.emitcode("lea rax, [rel {}]".format(litaddress))
                        self.emitcode("mov [{}], rax".format(node.lval.memoryaddress))
                    elif isinstance(node.literal1, NumericLiteral) and isinstance(node.literal1.pascaltype,
                                                                                  pascaltypes.RealType):
                        litaddress = self.tacgenerator.globalliteraltable.fetch(str(node.literal1.value)).memoryaddress
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
                        self.emitcode("mov rdi, printf_intfmt")
                        if params[0].paramval.pascaltype.size == 1:
                            destregister = "sil"
                        elif params[0].paramval.pascaltype.size == 2:
                            destregister = "si"
                        elif params[0].paramval.pascaltype.size == 4:
                            destregister = "esi"
                        elif params[0].paramval.pascaltype.size == 8:
                            destregister = "rsi"
                        else:
                            raise ASMGeneratorError("Invalid Size for _WRITEI/_WRITER")
                        self.emitcode("mov {}, [{}]".format(destregister, params[0].paramval.memoryaddress))
                        self.emitcode("mov rax, 0")
                        self.emitcode("call printf wrt ..plt")
                        self.emitcode("pop rsi")
                        self.emitcode("pop rdi")
                        del params[-1]
                    elif node.label.name == "_WRITER":
                        if node.numparams != 1:
                            raise ASMGeneratorError("Invalid numparams to _WRITER")
                        # Todo - see why using printf for reals was causing core dumps.
                        # self.emitcode("push rdi")
                        # self.emitcode("mov rdi, printf_realfmt")
                        self.emitcode("push rdi")
                        self.emitcode("XOR RDI, RDI")
                        self.emitcode("CALL fflush wrt ..plt", "flush printf buffer to keep printed items in order")
                        self.emitcode("pop rdi")
                        self.emitcode("movsd xmm0, [{}]".format(params[0].paramval.memoryaddress))
                        # self.emitcode("mov rax, 1", "1 floating point param")
                        # self.emitcode("call printf wrt ..plt")
                        # self.emitcode("pop rdi")
                        self.emitcode("call prtdbl")
                        del params[-1]
                    elif node.label.name == "_WRITES":
                        self.emitcode("push rdi")
                        self.emitcode("push rsi")
                        self.emitcode("mov rdi, printf_strfmt")
                        self.emitcode("mov rsi, [{}]".format(params[0].paramval.memoryaddress))
                        self.emitcode("mov rax, 0")
                        self.emitcode("call printf wrt ..plt")
                        self.emitcode("pop rsi")
                        self.emitcode("pop rdi")
                        del params[-1]
                    elif node.label.name == "_WRITECRLF":
                        self.emitcode("push rdi")
                        self.emitcode("mov rdi, printf_newln")
                        self.emitcode("mov rax, 0")
                        self.emitcode("call printf wrt ..plt")
                        self.emitcode("pop rdi")
                        self.emitcode("")
                    else:
                        raise ASMGeneratorError("Invalid System Function: {}".format(node.label.name))
                elif isinstance(node, TACBinaryNode):
                    # TODO - need to validate that this is an integer equivalent
                    if node.operator == TACOperator.MULTIPLY:
                        # TODO - handle something other than integers which are 4 bytes
                        self.emitcode("mov eax, [{}]".format(node.arg1.memoryaddress))
                        self.emitcode("mov r11d, [{}]".format(node.arg2.memoryaddress))
                        self.emitcode("imul eax, r11d")
                        self.emitcode("mov [{}], eax".format(node.result.memoryaddress))
                    elif node.operator == TACOperator.ADD:
                        # TODO - handle something other than integers which are 4 bytes
                        self.emitcode("mov eax, [{}]".format(node.arg1.memoryaddress))
                        self.emitcode("mov r11d, [{}]".format(node.arg2.memoryaddress))
                        self.emitcode("add eax, r11d")
                        self.emitcode("mov [{}], eax".format(node.result.memoryaddress))
                    elif node.operator == TACOperator.SUBTRACT:
                        # TODO - handle something other than integers which are 4 bytes
                        self.emitcode("mov eax, [{}]".format(node.arg1.memoryaddress))
                        self.emitcode("mov r11d, [{}]".format(node.arg2.memoryaddress))
                        self.emitcode("sub eax, r11d")
                        self.emitcode("mov [{}], eax".format(node.result.memoryaddress))
                    else:
                        raise Exception("I need an exception")
                    self.emitcode("jo _PASCAL_OVERFLOW_ERROR")
                else:
                    raise Exception("Some better exception")

            if totalstorageneeded > 0:
                self.emitcode("POP RBP")

    def generate_errorhandlingcode(self):
        # overflow
        self.emitcomment("overflow error")
        self.emitlabel("_PASCAL_OVERFLOW_ERROR")
        self.emitcode("push rdi")
        self.emitcode("mov rdi, stringerr_0")
        self.emitcode("mov rax, 0")
        self.emitcode("call printf wrt ..plt")
        self.emitcode("pop rdi")
        self.emitcode("jmp _PASCAL_EXIT")
        self.emitcomment("exit program")
        self.emitlabel("_PASCAL_EXIT")
        self.emitcomment("Need to flush the stdout buffer, as exiting does not do it..")
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

    def generate(self):
        self.generate_externs()
        self.generate_datasection()
        self.generate_textsection()
        self.asmfile.close()
        # break this out into better functions
        objectfilename = self.asmfilename[:-4] + ".o"
        exefilename = self.asmfilename[:-4]
        os.system("nasm -f elf64 -F dwarf -g -o nsm64.o nsm64.asm")
        os.system("nasm -f elf64 -F dwarf -g -o {} {}".format(objectfilename, self.asmfilename))
        # os.system("gcc {} -o {}".format(objectfilename, exefilename))
        os.system("gcc nsm64.o {} -o {}".format(objectfilename, exefilename))
