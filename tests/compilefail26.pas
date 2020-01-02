program compilefail26(output);
{redefined constant}

const pi = 3.14;
	negpi = -pi;
	pi = 3.1415;

begin
	writeln(pi);
	writeln(negpi);
end.
