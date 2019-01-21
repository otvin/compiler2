import sys

from lexer import Lexer

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

    f = open(infilename, "r")
    print(f.read())
    f.close()

    for i in l.tokenstream:
        print(i)


if __name__ == '__main__':
    main()