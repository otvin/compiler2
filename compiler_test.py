import os
import sys
import compiler

NUM_ATTEMPTS = 0
NUM_SUCCESSES = 0
TEST_FPC_INSTEAD = False  # switch to true to validate the .out files using fpc


def compare_two_files(actualfile, expectedfile, printdiffs=False):
    testfile1 = open(actualfile, "r")
    testvalue1 = testfile1.read()
    testfile1.close()

    testfile2 = open(expectedfile, "r")
    testvalue2 = testfile2.read()
    testfile2.close()

    if (testvalue1 != testvalue2) and printdiffs:
        print("ACTUAL " + actualfile)
        print(testvalue1)
        print("EXPECTED " + expectedfile)
        print(testvalue2)

    return testvalue1 == testvalue2


def dotest2(pascal_filename, numparamfiles=0, pipefile=False, paramfile_comparelist=None):
    assert pascal_filename[-4:] == ".pas"
    assert numparamfiles >= 0
    assert isinstance(pipefile, bool)
    assert paramfile_comparelist is None or isinstance(paramfile_comparelist, list)

    global NUM_ATTEMPTS
    global NUM_SUCCESSES

    NUM_ATTEMPTS += 1

    try:
        fileroot = pascal_filename[:-4]

        asmfilename = fileroot + ".asm"
        objfilename = fileroot + ".o"
        exefilename = fileroot
        stdoutfilename = fileroot + ".testoutput"
        resultfilename = fileroot + ".out"

        paramfilestr = ""
        for i in range(numparamfiles):
            paramfilestr = " " + fileroot + "_paramfile" + str(i) + ".file"

        pipefilestr = ""
        if pipefile:
            pipefilestr = " < " + fileroot + "_pipein" + ".file"

        if not TEST_FPC_INSTEAD:
            compiler.compile(pascal_filename, asmfilename=asmfilename, objfilename=objfilename, exefilename=exefilename)
        else:
            os.system("fpc -Miso -v0 {}".format(pascal_filename))

        exestr = "./{} {} {} > {}".format(exefilename, paramfilestr, pipefilestr, stdoutfilename)
        os.system(exestr)

        # compare the files
        passed = True  # assume success

        if not compare_two_files(stdoutfilename, resultfilename):
            passed = False
            print("FAIL: {}".format(pascal_filename))
            compare_two_files(stdoutfilename, resultfilename, True)

        if paramfile_comparelist is not None:
            for i in paramfile_comparelist:
                assert isinstance(i, int)
                actualfilename = fileroot + "_paramfile" + str(i) + ".file"
                expectedfilename = fileroot + "_comparefile" + str(i) + ".file"
                if not compare_two_files(actualfilename, expectedfilename):
                    if passed:
                        passed = False
                        print("FAIL: {}".format(pascal_filename))
                    compare_two_files(actualfilename, expectedfilename, True)

        if passed:
            if not TEST_FPC_INSTEAD:
                print("PASS: {}".format(pascal_filename))
            else:
                print("FPC PASS: {}".format(pascal_filename))

            # remove the files from passed tests; we will leave the files from failed tests so we can debug
            if not TEST_FPC_INSTEAD:
                os.system("rm {}".format(asmfilename))
                os.system("rm {}".format(objfilename))
            os.system("rm {}".format(exefilename))
            os.system("rm {}".format(stdoutfilename))
            if paramfile_comparelist is not None:
                for i in paramfile_comparelist:
                    actualfilename = fileroot + "_paramfile" + str(i) + ".file"
                    os.system("rm {}".format(actualfilename))

            NUM_SUCCESSES += 1

    except Exception as e:  # pragma: no cover
        print("FAIL: {}".format(pascal_filename))
        print(e)


def dotest(infilename, resultfilename):
    dotest2(infilename)


def do_compilefailtest(infilename, resultfilename):
    # For testing situations where the file fails to compile

    global NUM_ATTEMPTS
    global NUM_SUCCESSES

    if not TEST_FPC_INSTEAD:
        # FPC errors are totally different so don't try to test those

        NUM_ATTEMPTS += 1

        try:
            # the carriage return is included in the output files to end the line
            asmfilename = infilename[:-4] + ".asm"
            comparestr = compiler.compile(infilename, asmfilename=asmfilename).rstrip()

            if os.path.exists(asmfilename):
                os.system("rm {}".format(asmfilename))

            resultfile = open(resultfilename, "r")
            resultvalue = resultfile.read().rstrip()
            resultfile.close()

            if resultvalue == comparestr:
                print("PASS: {0}".format(infilename))
                NUM_SUCCESSES += 1
            else:
                print("Actual: " + comparestr)
                print("Expected: " + resultvalue)
                print("FAIL: {0}".format(infilename))
        except Exception as e:
            print("FAIL: {0}".format(infilename))
            print(e)

def do_compilefail_bugfixtest(numstr):
    # some bugfix tests are compile fail tests
    global ONLYTEST
    if ONLYTEST == "" or ONLYTEST == "bugfix":
        pasfile = "tests/testbugfix" + numstr + ".pas"
        outfile = "tests/testbugfix" + numstr + ".out"
        do_compilefailtest(pasfile, outfile)

def generate_test_list(topic, start, end):
    testlist = []
    for i in range(start, end + 1):
        test = topic
        if i < 10:
            test += "0"
        test += str(i)
        testlist.append(test)
    return testlist

ONLYTEST = ""
def run_test_list(topic, start, end):
    global ONLYTEST
    if ONLYTEST == "" or ONLYTEST == topic:
        testlist = generate_test_list(topic, start, end)
        for test in testlist:
            pasfile = "tests/test" + test + ".pas"
            outfile = "tests/test" + test + ".out"
            dotest(pasfile, outfile)

def run_compilefail_test_list(start, end):
    global ONLYTEST
    if ONLYTEST == "" or ONLYTEST == "compilefail":
        testlist = generate_test_list("compilefail", start, end)
        for test in testlist:
            pasfile = "tests/" + test + ".pas"
            outfile = "tests/" + test + ".out"
            do_compilefailtest(pasfile, outfile)


def main(onlytest=""):
    global NUM_ATTEMPTS
    global NUM_SUCCESSES
    global ONLYTEST

    ONLYTEST = onlytest

    run_test_list("array", 1, 23)
    run_test_list("assign", 1, 1)
    run_test_list("boolean", 1, 2)
    run_test_list("bugfix", 1, 1)
    do_compilefail_bugfixtest("02")
    # note testbyref06 in Compiler2 was "known_bug1.pas" in the old Compiler suite
    run_test_list("bugfix", 3, 3)
    run_test_list("byref", 1, 6)
    run_test_list("char", 1, 3)
    run_test_list("comments", 1, 1)
    run_test_list("const", 1, 6)
    run_test_list("divide", 1, 1)

    if ONLYTEST == "" or ONLYTEST == "files":
        dotest2("tests/testfiles01.pas", 1, False, [0])
        dotest2("tests/testfiles02.pas", 1, False, [0])
        dotest2("tests/testfiles03.pas", 1, False, [0])

    run_test_list("for", 1, 5)
    run_test_list("fpmath", 1, 7)
    run_test_list("functions", 1, 11)
    run_test_list("functions", 13, 17)
    run_test_list("globalvar", 1, 3)
    run_test_list("idiv", 1, 2)
    run_test_list("if", 1, 3)
    run_test_list("localvar", 1, 2)
    run_test_list("math", 1, 7)
    run_test_list("misc", 1, 1)
    run_test_list("mod", 1, 2)
    run_test_list("ord", 1, 6)
    # note testprocedure02 was "testproc01" in the old Compiler suite
    run_test_list("procedure", 1, 8)
    run_test_list("real", 1, 8)
    run_test_list("recursion", 1, 1)
    run_test_list("relop", 1, 6)
    run_test_list("repeat", 1, 2)
    run_test_list("scope", 1, 3)
    run_test_list("sqrt", 1, 2)
    run_test_list("string", 1, 1)
    run_test_list("string", 3, 3)
    run_test_list("string", 5, 11)
    run_test_list("typedef", 1, 13)
    run_test_list("while", 1, 3)
    run_test_list("write", 1, 2)
    run_test_list("writeln", 1, 3)

    run_compilefail_test_list(1, 76)

    # tests from old compiler not yet running in compiler2
    # dotest("tests/testconcat01.pas", "tests/testconcat01.out")
    # dotest("tests/testconcat02.pas", "tests/testconcat02.out")
    # dotest("tests/testconcat03.pas", "tests/testconcat03.out")
    # dotest("tests/testconcat04.pas", "tests/testconcat04.out")
    # dotest("tests/testconcat05.pas", "tests/testconcat05.out")
    # dotest("tests/testfunc12.pas", "tests/testfunc12.out")
    # dotest("tests/testproc02.pas", "tests/testproc02.out")
    # dotest("tests/testproc03.pas", "tests/testproc03.out")
    # dotest("tests/testproc04.pas", "tests/testproc04.out")
    # dotest("tests/teststring02.pas", "tests/teststring02.out")
    # dotest("tests/teststring04.pas", "tests/teststring04.out")

    print("Tests Attempted: " + str(NUM_ATTEMPTS))
    print("Tests Succeeded: " + str(NUM_SUCCESSES))


if __name__ == '__main__':  # pragma: no cover
    onlytest = ""
    if len(sys.argv) >= 2:
        if sys.argv[1].lower() == "fpc":
            TEST_FPC_INSTEAD = True
        else:
            onlytest = sys.argv[1].lower()
    main(onlytest)
