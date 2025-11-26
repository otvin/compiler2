import os
import sys
import compiler
import glob

num_attempts = 0
num_successes = 0


def list_files(directory, mask="*"):
    # written by chatGPT
    """Return a list of file names in the given directory matching the mask."""
    return [
        f
        for f in glob.glob(os.path.join(directory, mask))
        if os.path.isfile(f)
    ]


def compare_two_files(actual_file, expected_file, print_differences=False):
    test_file1 = open(actual_file, "r")
    test_value1 = test_file1.read()
    test_file1.close()

    test_file2 = open(expected_file, "r")
    test_value2 = test_file2.read()
    test_file2.close()

    if (test_value1 != test_value2) and print_differences:
        print("ACTUAL " + actual_file)
        print(test_value1)
        print("EXPECTED " + expected_file)
        print(test_value2)

    return test_value1 == test_value2


def do_test(pascal_filename, number_parameter_files=0, pipe_file=False, parameter_file_compare_list=None):
    assert pascal_filename[-4:] == ".pas", "compiler_test.do_test: invalid file name: {}".format(pascal_filename)
    assert number_parameter_files >= 0
    assert isinstance(pipe_file, bool)
    assert parameter_file_compare_list is None or isinstance(parameter_file_compare_list, list)

    global num_attempts
    global num_successes

    num_attempts += 1

    try:
        file_root = pascal_filename[:-4]

        assembly_file_name = file_root + ".asm"
        object_file_name = file_root + ".o"
        executable_file_name = file_root
        stdout_file_name = file_root + ".testoutput"
        result_file_name = file_root + ".out"
        warnings_file_name = file_root + ".warnings"

        parameter_file_string = ""
        for i in range(number_parameter_files):
            parameter_file_string = " " + file_root + "_parameter_file" + str(i) + ".file"

        pipe_file_string = ""
        if pipe_file:
            pipe_file_string = " < " + file_root + "_pipe_in" + ".file"

        compare_string = compiler.do_compile(pascal_filename, assembly_file_name=assembly_file_name,
                                             object_file_name=object_file_name,
                                             executable_file_name=executable_file_name).rstrip()

        executable_string = "./{} {} {} > {}".format(executable_file_name, parameter_file_string, pipe_file_string,
                                                     stdout_file_name)
        os.system(executable_string)

        # compare the files
        passed = True  # assume success

        if not compare_two_files(stdout_file_name, result_file_name):
            passed = False
            print("FAIL: {}".format(pascal_filename))
            compare_two_files(stdout_file_name, result_file_name, True)

        if parameter_file_compare_list is not None:
            for i in parameter_file_compare_list:
                assert isinstance(i, int)
                actual_result_file_name = file_root + "_parameter_file" + str(i) + ".file"
                expected_result_file_name = file_root + "_comparefile" + str(i) + ".file"
                if not compare_two_files(actual_result_file_name, expected_result_file_name):
                    if passed:
                        passed = False
                        print("FAIL: {}".format(pascal_filename))
                    compare_two_files(actual_result_file_name, expected_result_file_name, True)

        warning_string = ""
        if os.path.exists(warnings_file_name):
            warnings_file = open(warnings_file_name, "r")
            warning_string = warnings_file.read().rstrip()
            warnings_file.close()
        if compare_string != warning_string:
            passed = False
            print("FAIL: {}".format(pascal_filename))
            print("Actual warnings: {}".format(compare_string))
            print("Expected warnings: {}".format(warning_string))

        if passed:
            print("PASS: {}".format(pascal_filename))

            # remove the files from passed tests; we will leave the files from failed tests so we can debug
            os.system("rm {}".format(assembly_file_name))
            os.system("rm {}".format(object_file_name))
            os.system("rm {}".format(executable_file_name))
            os.system("rm {}".format(stdout_file_name))
            if parameter_file_compare_list is not None:
                for i in parameter_file_compare_list:
                    actual_file_name = file_root + "_parameter_file" + str(i) + ".file"
                    os.system("rm {}".format(actual_file_name))

            num_successes += 1

    except Exception as e:  # pragma: no cover
        print("FAIL: {}".format(pascal_filename))
        print(e)


def do_compile_fail_test(input_file_name):
    # For testing situations where the file fails to do_compile
    assert input_file_name[-4:] == ".pas", "compiler_test.do_compile_fail_test: invalid file name: {}".format(
        input_file_name)

    global num_attempts
    global num_successes

    num_attempts += 1

    try:
        # the carriage return is included in the output files to end the line
        result_file_name = input_file_name[:-4] + ".out"
        assembly_file_name = input_file_name[:-4] + ".asm"
        compare_str = compiler.do_compile(input_file_name, assembly_file_name=assembly_file_name).rstrip()

        if os.path.exists(assembly_file_name):
            os.system("rm {}".format(assembly_file_name))

        result_file = open(result_file_name, "r")
        result_value = result_file.read().rstrip()
        result_file.close()

        if result_value == compare_str:
            print("PASS: {0}".format(input_file_name))
            num_successes += 1
        else:
            print("FAIL: {0}".format(input_file_name))
            print("Actual: " + compare_str)
            print("Expected: " + result_value)
    except Exception as e:
        print("FAIL: {0}".format(input_file_name))
        print(e)


def main(only_test=""):
    global num_attempts
    global num_successes

    test_file_list = list_files("tests", "test{}*pas".format(only_test))
    test_file_list.sort()
    for filename in test_file_list:
        if "files" in filename:
            do_test(filename, 1, False, [0])
        else:
            do_test(filename)

    if only_test == "" or only_test == "compilefail":
        compile_fail_list = list_files("tests", "compilefail*pas")
        compile_fail_list.sort()
        for filename in compile_fail_list:
            do_compile_fail_test(filename)

    print("Tests Attempted: " + str(num_attempts))
    print("Tests Succeeded: " + str(num_successes))


if __name__ == '__main__':  # pragma: no cover
    onlytest = ""
    if len(sys.argv) >= 2:
        onlytest = sys.argv[1].lower()
    main(onlytest)
