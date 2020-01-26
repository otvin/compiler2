program compilefail59(output);
{validate arrays of one type cannot be passed as parameter as an array of a different type}

type
	littlearr = array[1..5] of boolean;
	bigarr = array[1..50] of integer;

var
	l:littlearr; b:bigarr;

procedure printlittlearr(a:littlearr);
begin
	writeln;
end;

begin
	printlittlearr(b);
end.
