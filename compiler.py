import sys
import traceback

from lexer import Lexer
from parser import Parser
from tac_ir import TACGenerator
from asmgenerator import AssemblyGenerator


def do_compile(input_file_name, assembly_file_name=None, object_file_name=None, executable_file_name=None,
               verbose_flag=False):

    return_str = ""

    if assembly_file_name is None:
        assembly_file_name = input_file_name[:-4] + ".asm"
    if object_file_name is None:
        object_file_name = assembly_file_name[:-4] + ".o"
    if executable_file_name is None:
        executable_file_name = assembly_file_name[:-4]

    lexer = Lexer(input_file_name)
    try:
        lexer.lex()
    except Exception as err:
        if verbose_flag:  # set to True to debug
            traceback.print_exc()
        return_str += str(err)
        return return_str

    if verbose_flag:
        print("LEXER OUTPUT")
        for i in lexer.tokenstream:
            print(str(i))

    p = Parser(lexer.tokenstream)
    try:
        p.parse()
    except Exception as err:
        if verbose_flag:  # set to True to debug
            traceback.print_exc()
        return_str += str(err)
        return return_str

    if verbose_flag:
        print("\n\nPARSER OUTPUT")
        print(p.AST.rpn_print(0))

    if len(p.parse_error_list) > 0:
        raise Exception("I need to display the compiler errors")

    if verbose_flag:
        print("LITERALS:")
        for q in p.literal_table:
            print(q)
        print("\n\n")
        print("symbols")
        p.AST.dump_symbol_tables()

    g = TACGenerator(p.literal_table)

    if verbose_flag:
        print("Literals again:")
        for q in g.global_literal_table:
            print(q)

    try:
        g.generate(p.AST)
    except Exception as err:
        if verbose_flag:  # set to True to debug
            g.print_blocks()
            traceback.print_exc()
        for warning_str in g.warnings_list:
            return_str += warning_str
        return_str += str(err)
        return return_str

    for warning_str in g.warnings_list:
        return_str += warning_str

    if verbose_flag:
        print("\n\nTHREE-ADDRESS CODE")
        g.print_blocks()

    ag = AssemblyGenerator(assembly_file_name, g)
    try:
        ag.generate(object_file_name, executable_file_name)
    except Exception as err:
        if verbose_flag:  # set to True to debug
            traceback.print_exc()
        return_str += str(err)
        return return_str
    return return_str


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
        verbose_flag_parameter = True
        input_file_name_parameter = sys.argv[2]
    else:
        verbose_flag_parameter = False
        input_file_name_parameter = sys.argv[1]

    compiler_output_str = do_compile(input_file_name_parameter, verbose_flag=verbose_flag_parameter)
    print(compiler_output_str)
