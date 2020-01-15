program compilefail54(output);
{invalid subrange - wrong order}

type 

	Positive = 1..maxint;
	TwoBits = -25..25;
	Index = 0..50;
	oopsie = 5..2;

var 
	f:oopsie;

begin
	f := 3;
	writeln(f);
end.
