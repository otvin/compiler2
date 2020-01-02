program compilefail28(output);
{cannot define a constant using itself}

const pi = 3.14;
	negpi = -negpi;

begin
	writeln(pi);
	writeln(negpi);
end.
