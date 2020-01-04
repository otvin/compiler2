program compilefail37(output);
{non-boolean expression with and}

var i:real;

begin

	i := 3.14;
	if i or True then
		writeln('oops');

end.
