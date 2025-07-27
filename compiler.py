import sys
import traceback

from lexer import Lexer
from parser import Parser
from tac_ir import TACGenerator, TACException
from asmgenerator import AssemblyGenerator


def compile(infilename, asmfilename=None, objfilename=None, exefilename=None,
            verbose=False):

    retstr = ""

    if asmfilename is None:
        asmfilename = infilename[:-4] + ".asm"
    if objfilename is None:
        objfilename = asmfilename[:-4] + ".o"
    if exefilename is None:
        exefilename = asmfilename[:-4]

    lexer = Lexer(infilename)
    try:
        lexer.lex()
    except Exception as err:
        if verbose:  # set to True to debug
            traceback.print_exc()
        retstr += str(err)
        return retstr

    if verbose:
        print("LEXER OUTPUT")
        for i in lexer.tokenstream:
            print(str(i))

    p = Parser(lexer.tokenstream)
    try:
        p.parse()
    except Exception as err:
        if verbose:  # set to True to debug
            traceback.print_exc()
        retstr += str(err)
        return retstr

    if verbose:
        print("\n\nPARSER OUTPUT")
        p.AST.rpn_print(0)

    if len(p.parseerrorlist) > 0:
        raise Exception("I need to display the compiler errors")

    if verbose:
        print("LITERALS:")
        for q in p.literaltable:
            print(q)
        print("\n\n")
        print("symbols")
        p.AST.dump_symboltables()

    g = TACGenerator(p.literaltable)

    if verbose:
        print("Literals again:")
        for q in g.globalliteraltable:
            print(q)

    try:
        g.generate(p.AST)
    except Exception as err:
        if verbose:  # set to True to debug
            g.printblocks()
            traceback.print_exc()
        retstr += str(err)
        return retstr

    if verbose:
        print("\n\nTHREE-ADDRESS CODE")
        g.printblocks()

    ag = AssemblyGenerator(asmfilename, g)
    try:
        ag.generate(objfilename, exefilename)
    except Exception as err:
        if verbose:  # set to True to debug
            traceback.print_exc()
        retstr += str(err)
        return retstr
    return retstr


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 compiler.py [filename]")
        print("Or: python3 -V compiler.py [filename]   {for verbose mode}")
        sys.exit()

    if sys.argv[1] == '-V':
        if len(sys.argv) < 3:
            print("Usage: python3 compiler.py [filename]")
            print("Or: python3 -V compiler.py [filename]   {for verbose mode}")
            sys.exit()
        verboseparm = True
        infileparm = sys.argv[2]
    else:
        verboseparm = False
        infileparm = sys.argv[1]

    infilename = sys.argv[1]
    outstr = compile(infileparm, verbose=verboseparm)
    print(outstr)
