import os
import sys
import compiler
import glob

NUM_ATTEMPTS = 0
NUM_SUCCESSES = 0

def list_files(directory, mask="*"):
    # written by chatGPT
    """Return a list of file names in the given directory matching the mask."""
    return [
        f
        for f in glob.glob(os.path.join(directory, mask))
        if os.path.isfile(f)
    ]

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


def dotest(pascal_filename, numparamfiles=0, pipefile=False, paramfile_comparelist=None):
    assert pascal_filename[-4:] == ".pas", "compiler_test.dotest: invalid file name: {}".format(pascal_filename)
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
        warningsfilename = fileroot + ".warnings"

        paramfilestr = ""
        for i in range(numparamfiles):
            paramfilestr = " " + fileroot + "_paramfile" + str(i) + ".file"

        pipefilestr = ""
        if pipefile:
            pipefilestr = " < " + fileroot + "_pipein" + ".file"

        comparestr = compiler.compile(pascal_filename, asmfilename=asmfilename, objfilename=objfilename, exefilename=exefilename).rstrip()

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

        warnstr = ""
        if os.path.exists(warningsfilename):
            warningsfile = open(warningsfilename, "r")
            warnstr = warningsfile.read().rstrip()
            warningsfile.close()
        if comparestr != warnstr:
            passed = False
            print("FAIL: {}".format(pascal_filename))
            print("Actual warnings: {}".format(comparestr))
            print("Expected warnings: {}".format(warnstr))

        if passed:
            print("PASS: {}".format(pascal_filename))

            # remove the files from passed tests; we will leave the files from failed tests so we can debug
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



def do_compilefailtest(infilename):
    # For testing situations where the file fails to compile
    assert infilename[-4:] == ".pas", "compiler_test.do_compilefailtest: invalid file name: {}".format(infilename)

    global NUM_ATTEMPTS
    global NUM_SUCCESSES

    NUM_ATTEMPTS += 1

    try:
        # the carriage return is included in the output files to end the line
        resultfilename = infilename[:-4] + ".out"
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
            print("FAIL: {0}".format(infilename))
            print("Actual: " + comparestr)
            print("Expected: " + resultvalue)
    except Exception as e:
        print("FAIL: {0}".format(infilename))
        print(e)

def main(onlytest=""):
    global NUM_ATTEMPTS
    global NUM_SUCCESSES

    testfilelist = list_files("tests", "test{}*pas".format(onlytest))
    testfilelist.sort()
    for filename in testfilelist:
        if "testfiles" in filename:
            dotest(filename, 1, False, [0])
        else:
            dotest(filename)

    if onlytest == "" or onlytest =="compilefail":
        compilefaillist = list_files("tests", "compilefail*pas")
        compilefaillist.sort()
        for filename in compilefaillist:
            do_compilefailtest(filename)

    print("Tests Attempted: " + str(NUM_ATTEMPTS))
    print("Tests Succeeded: " + str(NUM_SUCCESSES))


if __name__ == '__main__':  # pragma: no cover
    onlytest = ""
    if len(sys.argv) >= 2:
        onlytest = sys.argv[1].lower()
    main(onlytest)
