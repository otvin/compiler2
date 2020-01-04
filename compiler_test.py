import os
import sys
import compiler

NUM_ATTEMPTS = 0
NUM_SUCCESSES = 0
TEST_FPC_INSTEAD = False # switch to true to validate the .out files using fpc


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
            os.system("fpc -Miso -v0 {}".format(infilename))

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
            print("ACTUAL")
            print(testvalue)
            print("EXPECTED:")
            print(resultvalue)
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


def generate_test_list(topic, start, end):
    testlist = []
    for i in range(start, end + 1):
        test = topic
        if i < 10:
            test += "0"
        test += str(i)
        testlist.append(test)
    return testlist


def run_test_list(topic, start, end):
    testlist = generate_test_list(topic, start, end)
    for test in testlist:
        pasfile = "tests/test" + test + ".pas"
        outfile = "tests/test" + test + ".out"
        dotest(pasfile, outfile)


def run_compilefail_test_list(start, end):
    testlist = generate_test_list("compilefail", start, end)
    for test in testlist:
        pasfile = "tests/" + test + ".pas"
        outfile = "tests/" + test + ".out"
        do_compilefailtest(pasfile, outfile)


def main():
    global NUM_ATTEMPTS
    global NUM_SUCCESSES

    run_test_list("assign", 1, 1)
    run_test_list("boolean", 1, 2)
    run_test_list("bugfix", 1, 1)
    # note testbyref06 in Compiler2 was "known_bug1.pas" in the old Compiler suite
    run_test_list("byref", 1, 6)
    run_test_list("comments", 1, 1)
    run_test_list("const", 1, 4)
    run_test_list("divide", 1, 1)
    run_test_list("fpmath", 1, 7)
    run_test_list("functions", 1, 11)
    run_test_list("functions", 13, 15)
    run_test_list("globalvar", 1, 3)
    run_test_list("idiv", 1, 2)
    run_test_list("if", 1, 3)
    run_test_list("localvar", 1, 2)
    run_test_list("math", 1, 6)
    run_test_list("misc", 1, 1)
    run_test_list("mod", 1, 2)
    # note testprocedure02 was "proc01" in the old Compiler suite
    run_test_list("procedure", 1, 7)
    run_test_list("real", 1, 8)
    run_test_list("recursion", 1, 1)
    run_test_list("relop", 1, 4)
    run_test_list("repeat", 1, 2)
    run_test_list("scope", 1, 1)
    run_test_list("scope", 3, 3)
    run_test_list("sqrt", 1, 2)
    run_test_list("while", 1, 3)
    run_test_list("write", 1, 1)
    run_test_list("writeln", 1, 3)

    run_compilefail_test_list(1, 37)

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
    # dotest("tests/testscope02.pas", "tests/testscope02.out")
    # dotest("tests/teststring01.pas", "tests/teststring01.out")
    # dotest("tests/teststring02.pas", "tests/teststring02.out")
    # dotest("tests/teststring03.pas", "tests/teststring03.out")
    # dotest("tests/teststring04.pas", "tests/teststring04.out")

    print("Tests Attempted: " + str(NUM_ATTEMPTS))
    print("Tests Succeeded: " + str(NUM_SUCCESSES))


if __name__ == '__main__':  # pragma: no cover
    if len(sys.argv) >= 2:
        if sys.argv[1].lower() == "fpc":
            TEST_FPC_INSTEAD = True

    main()
