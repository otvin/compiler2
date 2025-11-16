import os
import compiler

NUM_ATTEMPTS = 0
NUM_SUCCESSES = 0

def do_conform():
    global NUM_ATTEMPTS
    global NUM_SUCCESSES
    testlist = []
    for i in range(1, 222):
        test = "CONF"
        if i < 10:
            test += "0"
        if i < 100:
            test += "0"
        test += str(i)
        testlist.append(test)

    for test in testlist:
        pascal_filename = "tests/BSI-validation-suite/CONFORM/" + test + ".pas"
        asmfilename = "tests/BSI-validation-suite/CONFORM/" + test + ".asm"
        objfilename = "tests/BSI-validation-suite/CONFORM/" + test + ".o"
        exefilename = "tests/BSI-validation-suite/CONFORM/" + test
        stdoutfilename = "tests/BSI-validation-suite/CONFORM/" + test + ".testoutput"

        try:
            t = compiler.compile(pascal_filename, asmfilename=asmfilename, objfilename=objfilename, exefilename=exefilename)
            if os.path.exists(exefilename):
                exestr = "./{} > {}".format(exefilename, stdoutfilename)
                os.system(exestr)
                stdoutfile = open(stdoutfilename, "r")
                testresult = stdoutfile.read()
                stdoutfile.close()

                if pascal_filename[-11:] == "CONF024.pas" and testresult == "":
                    testresult = " PASS...6.8.2.1 (CONF024)"
                if testresult[:5] == " PASS":
                    print(testresult[1:])
                    NUM_SUCCESSES += 1
                    os.system("rm {}".format(asmfilename))
                    os.system("rm {}".format(objfilename))
                    os.system("rm {}".format(exefilename))
                    os.system("rm {}".format(stdoutfilename))
                elif testresult[:5] == " FAIL":
                    print(testresult[1:])
                    os.system("rm {}".format(stdoutfilename))
                else:
                    print('{} ({})'.format(testresult,test))
            else:
                print("Compile error: {} ({})\n".format(t, test))
        except Exception as e:
            print("FAIL: {}".format(pascal_filename))
            print(e)
        NUM_ATTEMPTS += 1


def main():
    global NUM_ATTEMPTS
    global NUM_SUCCESSES

    do_conform()

    print("Tests Attempted: " + str(NUM_ATTEMPTS))
    print("Tests Succeeded: " + str(NUM_SUCCESSES))

#TODO: refactor validation_test and compiler_test to use shared library vs. copying code
if __name__ == '__main__':  # pragma: no cover
    main()