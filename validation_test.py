import os
import compiler

num_attempts = 0
num_successes = 0


def do_conform():
    global num_attempts
    global num_successes
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
        assembly_file_name = "tests/BSI-validation-suite/CONFORM/" + test + ".asm"
        object_file_name = "tests/BSI-validation-suite/CONFORM/" + test + ".o"
        executable_file_name = "tests/BSI-validation-suite/CONFORM/" + test
        stdout_file_name = "tests/BSI-validation-suite/CONFORM/" + test + ".testoutput"

        try:
            t = compiler.do_compile(pascal_filename, assembly_file_name=assembly_file_name,
                                    object_file_name=object_file_name,
                                    executable_file_name=executable_file_name)
            if os.path.exists(executable_file_name):
                executable_string = "./{} > {}".format(executable_file_name, stdout_file_name)
                os.system(executable_string)
                stdout_file = open(stdout_file_name, "r")
                test_result = stdout_file.read()
                stdout_file.close()

                if pascal_filename[-11:] == "CONF024.pas" and test_result == "":
                    test_result = " PASS...6.8.2.1 (CONF024)"
                if test_result[:5] == " PASS":
                    print(test_result[1:])
                    num_successes += 1
                    os.system("rm {}".format(assembly_file_name))
                    os.system("rm {}".format(object_file_name))
                    os.system("rm {}".format(executable_file_name))
                    os.system("rm {}".format(stdout_file_name))
                elif test_result[:5] == " FAIL":
                    print(test_result[1:])
                    os.system("rm {}".format(stdout_file_name))
                else:
                    print('{} ({})'.format(test_result, test))
            else:
                print("Compile error: {} ({})\n".format(t, test))
        except Exception as e:
            print("FAIL: {}".format(pascal_filename))
            print(e)
        num_attempts += 1


def main():
    global num_attempts
    global num_successes

    do_conform()

    print("Tests Attempted: " + str(num_attempts))
    print("Tests Succeeded: " + str(num_successes))


# TODO: refactor validation_test and compiler_test to use shared library vs. copying code
if __name__ == '__main__':  # pragma: no cover
    main()
