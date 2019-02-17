import sys

from lexer import Lexer
from parser import Parser
from tac_ir import TACGenerator
from asmgenerator import AssemblyGenerator


def main():
    debugmode = False

    if len(sys.argv) < 2:
        print("Usage: python3 compiler.py [filename]")
        sys.exit()

    infilename = sys.argv[1]
    lexer = Lexer(infilename)
    try:
        lexer.lex()
    except Exception as err:
        if debugmode:  # set to True to debug
            print(err)
        else:
            print(str(err))
        sys.exit()

    print("LEXER OUTPUT")
    for i in lexer.tokenstream:
        print(str(i))

    p = Parser(lexer.tokenstream)
    try:
        p.parse()
    except Exception as err:
        if debugmode:  # set to True to debug
            print(err)
        else:
            print(str(err))
        sys.exit()

    print("\n\nPARSER OUTPUT")
    p.AST.rpn_print(0)

    if len(p.parseerrorlist) > 0:
        raise("I need to display the compiler errors")

    g = TACGenerator(p.literaltable)
    g.generate(p.AST)
    print("\n\nTHREE-ADDRESS CODE")
    g.printblocks()

    asmfilename = infilename[:-4] + ".asm"
    ag = AssemblyGenerator(asmfilename, g)
    ag.generate()

    # f = open(infilename, "r")
    # print(f.read())
    # f.close()

    # for i in l.tokenstream:
    #    print(i)
    # g = open('test.lex','w')
    # for i in l.tokenstream:
    #    g.write(str(i))

if __name__ == '__main__':
    main()