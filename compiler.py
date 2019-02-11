import sys

from lexer import Lexer
from parser import Parser
from tac_ir import TACGenerator

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 compiler.py [filename]")
        sys.exit()

    infilename = sys.argv[1]
    l = Lexer(infilename)
    try:
        l.lex()
    except Exception as err:
        if False:  # set to True to debug
            print(err)
        else:
            print(str(err))
        sys.exit()

    p = Parser(l.tokenstream)
    try:
        p.parse()
    except Exception as err:
        if False:  # set to True to debug
            print(err)
        else:
            print(str(err))
        sys.exit()

    p.AST.rpn_print(0)

    g = TACGenerator(p.literaltable)
    g.generate(p.AST)
    g.printblocks()

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