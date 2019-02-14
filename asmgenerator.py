import os
from tac_ir import TACBlock, TACNode, TACLabelNode, TACParamNode, TACCallSystemFunctionNode, TACUnaryLiteralNode, \
    TACOperator


class AssemblyGenerator:
    def __init__(self, asmfilename, tacblocks):
        # tacblocks is a list of TACBlock objects
        self.asmfilename = asmfilename
        self.asmfile = open(asmfilename, 'w')
        self.tacblocks = tacblocks

    def emit(self, s):
        self.asmfile.write(s)

    def emitln(self, s):
        self.emit(s + '\n')

    def emitcode(self, s):
        self.emitln('\t' + s)

    def emitlabel(self, labelname):
        self.emitln(labelname + ":")

    def emitsection(self, sectionname):
        self.emitln("section .{}".format(sectionname))

    def emitcomment(self, commentstr):
        self.emitln("; {}".format(commentstr))

    def generate_externs(self):
        self.emitcode("extern printf")

    def generate_datasection(self):
        # this is static for now
        self.emitsection("data")
        self.emitcomment("support for write() commands")
        self.emitcode('printf_intfmt db "%ld%",0')
        self.emitcode('printf_newln db 10,0')

    def generate_code(self):
        params = []  # this is a stack of parameters

        for block in self.tacblocks:
            # todo - figure out how to manage the stack here for all the temporaries
            assert isinstance(block, TACBlock)
            for node in block.tacnodes:
                if isinstance(node, TACLabelNode):
                    self.emitlabel(node.label.name)
                elif isinstance(node, TACParamNode):
                    params.append(node)
                elif isinstance(node, TACUnaryLiteralNode):
                    if node.operator == TACOperator.ASSIGN:
                        # cheesy hack - this will need to store wherever the temporaries are assigned
                        self.emitcode("mov rax, {}".format(node.literal1.value))
                elif isinstance(node, TACCallSystemFunctionNode):
                    if node.label.name == "_WRITEI":
                        if node.numparams != 1:
                            raise Exception("Invalid numparams to _WRITEI")  # TODO - use a better Exception
                        self.emitcode("mov rdi, printf_intfmt")
                        # cheesy hack - need to go to wherever the temporaries are assigned
                        self.emitcode("mov rsi, rax")
                        self.emitcode("mov rax, 0")
                        self.emitcode("call printf wrt ..plt")
                        del params[-1]
                else:
                    raise Exception("Some better exception")

    def generate_textsection(self):
        self.emitsection("text")
        self.emitcode("global main")
        self.generate_code()
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
