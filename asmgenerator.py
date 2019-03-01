import os
from tac_ir import TACBlock, TACLabelNode, TACParamNode, TACCallSystemFunctionNode, TACUnaryLiteralNode, \
    TACOperator, TACGenerator, TACCommentNode, TACBinaryNode
from symboltable import StringLiteral


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

    def generate_datasection(self):
        self.emitsection("data")
        self.emitcomment("support for write() commands")
        self.emitcode('printf_intfmt db "%d",0')
        self.emitcode('printf_strfmt db "%s",0')
        self.emitcode('printf_newln db 10,0')
        if len(self.tacgenerator.globalliteraltable) > 0:
            nextid = 0
            for lit in self.tacgenerator.globalliteraltable:
                assert isinstance(lit, StringLiteral)
                litname = 'stringlit_{}'.format(nextid)
                nextid += 1
                if len(lit.value) > 255:
                    raise ASMGeneratorError("String literal {} exceeds 255 char max length.".format(lit.value))
                self.emitcode("{} db {} ,`{}`, 0".format(litname, str(len(lit.value) + 1),
                                                         lit.value.replace('`', '\\`')))
                lit.setaddress(litname)

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
                        litaddress = self.tacgenerator.globalliteraltable.fetch(node.literal1.value).memoryaddress
                        self.emitcode("lea rax, [rel {}]".format(litaddress))
                        self.emitcode("mov [{}], rax".format(node.lval.memoryaddress))
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
                        # TODO - see if we need to push rdi/rsi then pop them off after the printf call
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
                            raise ASMGeneratorError("Invalid Size for _WRITEI")
                        self.emitcode("mov {}, [{}]".format(destregister, params[0].paramval.memoryaddress))
                        self.emitcode("mov rax, 0")
                        self.emitcode("call printf wrt ..plt")
                        del params[-1]
                    elif node.label.name == "_WRITES":
                        self.emitcode("mov rdi, printf_strfmt")
                        self.emitcode("mov rsi, [{}]".format(params[0].paramval.memoryaddress))
                        self.emitcode("mov rax, 0")
                        self.emitcode("call printf wrt ..plt")
                        del params[-1]
                    else:
                        raise ASMGeneratorError("Invalid System Function: {}".format(node.label.name))
                elif isinstance(node, TACBinaryNode):
                    if node.operator == TACOperator.MULTIPLY:
                        # TODO - handle something other than integers which are 4 bytes
                        self.emitcode("mov eax, [{}]".format(node.arg1.memoryaddress))
                        self.emitcode("mov r11d, [{}]".format(node.arg2.memoryaddress))
                        self.emitcode("imul eax, r11d")
                        self.emitcode("mov [{}], eax".format(node.result.memoryaddress))
                    else:
                        raise Exception("I need an exception")
                else:
                    raise Exception("Some better exception")

            if totalstorageneeded > 0:
                self.emitcode("POP RBP")

    def generate_textsection(self):
        self.emitsection("text")
        self.emitcode("global main")
        self.generate_code()
        self.emitcomment("hack: need to flush the buffer.  A CRLF does it, but there should be a better way")
        self.emitcode("MOV RDI, printf_newln")
        self.emitcode("MOV RAX, 0")
        self.emitcode("CALL printf wrt ..plt")
        self.emitcode("XOR EDI, EDI", "Exit Program")
        self.emitcode("MOV EAX, 60")
        self.emitcode("SYSCALL")
        self.emitcode("ret")

    def generate(self):
        self.generate_externs()
        self.generate_datasection()
        self.generate_textsection()
        self.asmfile.close()
        # break this out into better functions
        objectfilename = self.asmfilename[:-4] + ".o"
        exefilename = self.asmfilename[:-4]
        os.system("nasm -f elf64 -F dwarf -g -o {} {}".format(objectfilename, self.asmfilename))
        os.system("gcc {} -o {}".format(objectfilename, exefilename))
