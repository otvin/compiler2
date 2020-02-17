program testfiles03(output, myout);
{test rewriting a file after writing to it.}

var myout:text;

begin
	rewrite(myout);
	writeln(myout, 30973);
	writeln(myout, 3.14159);
	rewrite(myout);
	writeln(myout, 'hi');
	writeln('done');
end.
