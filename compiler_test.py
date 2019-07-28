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
			os.system("fpc -v0 -o" + exefilename + " " + infilename)

		os.system("./" + exefilename + " > " + testoutputfilename)

		testfile = open(testoutputfilename, "r")
		testvalue = testfile.read()
		testfile.close()

		resultfile = open(resultfilename, "r")
		resultvalue = resultfile.read()
		resultfile.close()

		if resultvalue == testvalue:
			if not TEST_FPC_INSTEAD:
				print("PASS: " + infilename)
			else:
				print("FPC PASS: " + infilename)
			NUM_SUCCESSES += 1

			# remove the files from passed tests; we will leave the files from failed tests so we can debug
			if not TEST_FPC_INSTEAD:
				os.system("rm " + asmfilename)
				os.system("rm " + objfilename)
			os.system("rm " + exefilename)
			os.system("rm " + testoutputfilename)
		else:  # pragma: no cover
			print("FAIL: " + infilename)
	except Exception as e:  # pragma: no cover
		print("FAIL: " + infilename)
		print(e)


def main():
	global NUM_ATTEMPTS
	global NUM_SUCCESSES

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
	# dotest("tests/testfunc01.pas", "tests/testfunc01.out")
	# dotest("tests/testfunc02.pas", "tests/testfunc02.out")
	# dotest("tests/testfunc03.pas", "tests/testfunc03.out")
	# dotest("tests/testfunc04.pas", "tests/testfunc04.out")
	# dotest("tests/testfunc05.pas", "tests/testfunc05.out")
	# dotest("tests/testfunc06.pas", "tests/testfunc06.out")
	# dotest("tests/testfunc07.pas", "tests/testfunc07.out")
	# dotest("tests/testfunc08.pas", "tests/testfunc08.out")
	# dotest("tests/testfunc09.pas", "tests/testfunc09.out")
	# dotest("tests/testfunc10.pas", "tests/testfunc10.out")
	# dotest("tests/testfunc11.pas", "tests/testfunc11.out")
	# dotest("tests/testglobalvar01.pas", "tests/testglobalvar01.out")
	# dotest("tests/testglobalvar02.pas", "tests/testglobalvar02.out")
	# dotest("tests/testif01.pas", "tests/testif01.out")
	# dotest("tests/testif02.pas", "tests/testif02.out")
	# dotest("tests/testif03.pas", "tests/testif03.out")
	# dotest("tests/testlocalvar01.pas", "tests/testlocalvar01.out")
	# dotest("tests/testlocalvar02.pas", "tests/testlocalvar02.out")
	dotest("tests/testmath01.pas", "tests/testmath01.out")
	dotest("tests/testmath02.pas", "tests/testmath02.out")
	# dotest("tests/testmath03.pas", "tests/testmath03.out")
	# dotest("tests/testmath04.pas", "tests/testmath04.out")
	# dotest("tests/testproc01.pas", "tests/testproc01.out")
	# dotest("tests/testproc02.pas", "tests/testproc02.out")
	# dotest("tests/testproc03.pas", "tests/testproc03.out")
	# dotest("tests/testproc04.pas", "tests/testproc04.out")
	dotest("tests/testreal01.pas", "tests/testreal01.out")
	dotest("tests/testreal02.pas", "tests/testreal02.out")
	dotest("tests/testreal03.pas", "tests/testreal03.out")
	# dotest("tests/testreal04.pas", "tests/testreal04.out")
	# dotest("tests/testreal05.pas", "tests/testreal05.out")
	# dotest("tests/testreal06.pas", "tests/testreal06.out")
	# dotest("tests/testreal07.pas", "tests/testreal07.out")
	# dotest("tests/testreal08.pas", "tests/testreal08.out")
	# dotest("tests/testrecursion01.pas", "tests/testrecursion01.out")
	# dotest("tests/testrelop01.pas", "tests/testrelop01.out")
	# dotest("tests/testrelop02.pas", "tests/testrelop02.out")
	# dotest("tests/testscope01.pas", "tests/testscope01.out")
	# dotest("tests/testscope02.pas", "tests/testscope02.out")
	# dotest("tests/testscope03.pas", "tests/testscope03.out")
	# dotest("tests/teststring01.pas", "tests/teststring01.out")
	# dotest("tests/teststring02.pas", "tests/teststring02.out")
	# dotest("tests/teststring03.pas", "tests/teststring03.out")
	# dotest("tests/teststring04.pas", "tests/teststring04.out")
	# dotest("tests/testwhile01.pas", "tests/testwhile01.out")
	# dotest("tests/testwhile02.pas", "tests/testwhile02.out")
	dotest("tests/testwrite01.pas", "tests/testwrite01.out")
	dotest("tests/testwriteln01.pas", "tests/testwriteln01.out")
	dotest("tests/testwriteln02.pas", "tests/testwriteln02.out")
	dotest("tests/testwriteln03.pas", "tests/testwriteln03.out")

	print("Tests Attempted: " + str(NUM_ATTEMPTS))
	print("Tests Succeeded: " + str(NUM_SUCCESSES))


if __name__ == '__main__':  # pragma: no cover
	if len(sys.argv) >= 2:
		if sys.argv[1].lower() == "fpc":
			TEST_FPC_INSTEAD = True

	main()
