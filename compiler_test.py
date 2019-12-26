import os
import sys
import compiler

NUM_ATTEMPTS = 0
NUM_SUCCESSES = 0
TEST_FPC_INSTEAD = False  # switch to true to validate the .out files using fpc


def dotest(infilename, resultfilename):
    global NUM_ATTEMPTS
    global NUM_SUCCESSES

    NUM_ATTEMPTS += 1

    try:
        asmfilename = infilename[:-4] + ".asm"
        objfilename = infilename[:-4] + ".o"
        exefilename = infilename[:-4]
        testoutputfilename = exefilename + ".testoutput"

        if not TEST_FPC_INSTEAD:
            compiler.compile(infilename, asmfilename=asmfilename, objfilename=objfilename, exefilename=exefilename)
        else:
            os.system("fpc -v0 -o {0} {1}".format(exefilename, infilename))

        os.system("./{0} > {1}".format(exefilename, testoutputfilename))

        testfile = open(testoutputfilename, "r")
        testvalue = testfile.read()
        testfile.close()

        resultfile = open(resultfilename, "r")
        resultvalue = resultfile.read()
        resultfile.close()

        if resultvalue == testvalue:
            if not TEST_FPC_INSTEAD:
                print("PASS: {}".format(infilename))
            else:
                print("FPC PASS: {}".format(infilename))
            NUM_SUCCESSES += 1

            # remove the files from passed tests; we will leave the files from failed tests so we can debug
            if not TEST_FPC_INSTEAD:
                os.system("rm {}".format(asmfilename))
                os.system("rm {}".format(objfilename))
            os.system("rm {}".format(exefilename))
            os.system("rm {}".format(testoutputfilename))
        else:  # pragma: no cover
            print("FAIL: {}".format(infilename))
    except Exception as e:  # pragma: no cover
        print("FAIL: {}".format(infilename))
        print(e)


def do_compilefailtest(infilename, resultfilename):
    # For testing situations where the file fails to compile

    global NUM_ATTEMPTS
    global NUM_SUCCESSES

    if not TEST_FPC_INSTEAD:
        # FPC errors are totally different so don't try to test those

        NUM_ATTEMPTS += 1

        try:
            # the carriage return is included in the output files to end the line
            comparestr = compiler.compile(infilename) + "\n"
            # print(comparestr)

            # TODO remove any .asm file that is generated, as some compiler fails occur after some assembly is written.

            resultfile = open(resultfilename, "r")
            resultvalue = resultfile.read()
            resultfile.close()

            if resultvalue == comparestr:
                print("PASS: {0}".format(infilename))
                NUM_SUCCESSES += 1
            else:
                print("*" + comparestr + "*")
                print("&" + resultvalue + "&")
                print("FAIL: {0}".format(infilename))
        except Exception as e:
            print("FAIL: {0}".format(infilename))
            print(e)


def main():
    global NUM_ATTEMPTS
    global NUM_SUCCESSES

    dotest("tests/testassign01.pas", "tests/testassign01.out")
    dotest("tests/testboolean01.pas", "tests/testboolean01.out")
    dotest("tests/testbugfix01.pas", "tests/testbugfix01.out")
    # dotest("tests/testbyref01.pas", "tests/testbyref01.out")
    # dotest("tests/testbyref02.pas", "tests/testbyref02.out")
    # dotest("tests/testbyref03.pas", "tests/testbyref03.out")
    # dotest("tests/testbyref04.pas", "tests/testbyref04.out")
    dotest("tests/testcomments01.pas", "tests/testcomments01.out")
    # dotest("tests/testconcat01.pas", "tests/testconcat01.out")
    # dotest("tests/testconcat02.pas", "tests/testconcat02.out")
    # dotest("tests/testconcat03.pas", "tests/testconcat03.out")
    # dotest("tests/testconcat04.pas", "tests/testconcat04.out")
    # dotest("tests/testconcat05.pas", "tests/testconcat05.out")
    dotest("tests/testdivide01.pas", "tests/testdivide01.out")
    dotest("tests/testfunctions01.pas", "tests/testfunctions01.out")
    dotest("tests/testfunctions02.pas", "tests/testfunctions02.out")
    dotest("tests/testfunctions03.pas", "tests/testfunctions03.out")
    dotest("tests/testfunctions04.pas", "tests/testfunctions04.out")
    dotest("tests/testfunctions05.pas", "tests/testfunctions05.out")
    dotest("tests/testfunctions06.pas", "tests/testfunctions06.out")
    dotest("tests/testfunctions07.pas", "tests/testfunctions07.out")
    dotest("tests/testfunctions08.pas", "tests/testfunctions08.out")
    dotest("tests/testfunctions09.pas", "tests/testfunctions09.out")
    dotest("tests/testfunctions10.pas", "tests/testfunctions10.out")
    dotest("tests/testfunctions11.pas", "tests/testfunctions11.out")
    # dotest("tests/testfunc12.pas", "tests/testfunc12.out")
    dotest("tests/testfunctions13.pas", "tests/testfunctions13.out")
    dotest("tests/testglobalvar01.pas", "tests/testglobalvar01.out")
    dotest("tests/testglobalvar02.pas", "tests/testglobalvar02.out")
    dotest("tests/testglobalvar03.pas", "tests/testglobalvar03.out")
    dotest("tests/testidiv01.pas", "tests/testidiv01.out")
    dotest("tests/testidiv02.pas", "tests/testidiv02.out")
    dotest("tests/testif01.pas", "tests/testif01.out")
    dotest("tests/testif02.pas", "tests/testif02.out")
    dotest("tests/testif03.pas", "tests/testif03.out")
    dotest("tests/testlocalvar01.pas", "tests/testlocalvar01.out")
    dotest("tests/testlocalvar02.pas", "tests/testlocalvar02.out")
    dotest("tests/testmath01.pas", "tests/testmath01.out")
    dotest("tests/testmath02.pas", "tests/testmath02.out")
    dotest("tests/testmath03.pas", "tests/testmath03.out")
    dotest("tests/testmath04.pas", "tests/testmath04.out")
    dotest("tests/testmisc01.pas", "tests/testmisc01.out")
    dotest("tests/testmod01.pas", "tests/testmod01.out")
    dotest("tests/testmod02.pas", "tests/testmod02.out")
    # dotest("tests/testproc02.pas", "tests/testproc02.out")
    # dotest("tests/testproc03.pas", "tests/testproc03.out")
    # dotest("tests/testproc04.pas", "tests/testproc04.out")
    dotest("tests/testprocedure01.pas", "tests/testprocedure01.out")
    dotest("tests/testprocedure02.pas", "tests/testprocedure02.out") # was testproc01.pas in the "compiler" suite
    dotest("tests/testprocedure03.pas", "tests/testprocedure03.out")
    dotest("tests/testprocedure04.pas", "tests/testprocedure04.out")
    dotest("tests/testprocedure05.pas", "tests/testprocedure05.out")
    dotest("tests/testprocedure06.pas", "tests/testprocedure06.out")
    dotest("tests/testprocedure07.pas", "tests/testprocedure07.out")
    dotest("tests/testreal01.pas", "tests/testreal01.out")
    dotest("tests/testreal02.pas", "tests/testreal02.out")
    dotest("tests/testreal03.pas", "tests/testreal03.out")
    dotest("tests/testreal04.pas", "tests/testreal04.out")
    dotest("tests/testreal05.pas", "tests/testreal05.out")
    dotest("tests/testreal06.pas", "tests/testreal06.out")
    dotest("tests/testreal07.pas", "tests/testreal07.out")
    dotest("tests/testreal08.pas", "tests/testreal08.out")
    dotest("tests/testrecursion01.pas", "tests/testrecursion01.out")
    dotest("tests/testrelop01.pas", "tests/testrelop01.out")
    dotest("tests/testrelop02.pas", "tests/testrelop02.out")
    dotest("tests/testrelop03.pas", "tests/testrelop03.out")
    dotest("tests/testrelop04.pas", "tests/testrelop04.out")
    dotest("tests/testrepeat01.pas", "tests/testrepeat01.out")
    dotest("tests/testrepeat02.pas", "tests/testrepeat02.out")
    dotest("tests/testscope01.pas", "tests/testscope01.out")
    # dotest("tests/testscope02.pas", "tests/testscope02.out")
    dotest("tests/testscope03.pas", "tests/testscope03.out")
    # dotest("tests/teststring01.pas", "tests/teststring01.out")
    # dotest("tests/teststring02.pas", "tests/teststring02.out")
    # dotest("tests/teststring03.pas", "tests/teststring03.out")
    # dotest("tests/teststring04.pas", "tests/teststring04.out")
    dotest("tests/testwhile01.pas", "tests/testwhile01.out")
    dotest("tests/testwhile02.pas", "tests/testwhile02.out")
    dotest("tests/testwhile03.pas", "tests/testwhile03.out")
    dotest("tests/testwrite01.pas", "tests/testwrite01.out")
    dotest("tests/testwriteln01.pas", "tests/testwriteln01.out")
    dotest("tests/testwriteln02.pas", "tests/testwriteln02.out")
    dotest("tests/testwriteln03.pas", "tests/testwriteln03.out")

    do_compilefailtest("tests/compilefail01.pas", "tests/compilefail01.out")
    do_compilefailtest("tests/compilefail02.pas", "tests/compilefail02.out")
    do_compilefailtest("tests/compilefail03.pas", "tests/compilefail03.out")
    do_compilefailtest("tests/compilefail04.pas", "tests/compilefail04.out")
    do_compilefailtest("tests/compilefail05.pas", "tests/compilefail05.out")
    do_compilefailtest("tests/compilefail06.pas", "tests/compilefail06.out")
    do_compilefailtest("tests/compilefail07.pas", "tests/compilefail07.out")

    print("Tests Attempted: " + str(NUM_ATTEMPTS))
    print("Tests Succeeded: " + str(NUM_SUCCESSES))


if __name__ == '__main__':  # pragma: no cover
    if len(sys.argv) >= 2:
        if sys.argv[1].lower() == "fpc":
            TEST_FPC_INSTEAD = True

    main()
