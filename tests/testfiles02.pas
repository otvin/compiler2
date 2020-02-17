program testfiles02(output, myout);
{test writing different types of data to file passed in via program parameter}

var myout:text;

begin
	rewrite(myout);
	writeln(myout, 30973);
	writeln(myout, 3.14159);
	writeln(myout, TRUE);
	writeln(myout, 'Hello World! ', 'Goodbye World! ', 42);
	writeln(output, 'done');
end.
