program testfiles01(output, myout);
{test writing to an output file passed in via program parameter}

var myout:text;

begin
	rewrite(myout);
	{writing characters uses fputc which is simpler assembly}
	writeln(myout, 'x');
	writeln(output, 'x');	
end.
