program compilefail64(output);
{illegal subrange in an anonymous type}

var b : 4 .. 'q';

begin
	b := 7;
	writeln(b);
end.
