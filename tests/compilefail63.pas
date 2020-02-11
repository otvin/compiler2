program compilefail63(output);
{illegal subrange in an anonymous type}

var b : 3.17 .. 7.26;

begin
	b := 7;
	writeln(b);
end.
