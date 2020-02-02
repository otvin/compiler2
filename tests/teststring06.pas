program teststring06(output);
{test assignment of compatible string types}

type
	Length = 1..15;
	mystring = packed array[Length] of char;

	otherstring = packed array[1..15] of char;

var alpha:mystring; beta:otherstring;

begin
	alpha[1] := 'H';
	alpha[2] := 'e';
	alpha[3] := 'l';
	alpha[4] := 'l';
	alpha[5] := 'o';
	alpha[6] := ' ';
	alpha[7] := 'W';
	alpha[8] := 'o';
	alpha[9] := 'r';
	alpha[10]:= 'l';
	alpha[11]:= 'd';
	alpha[12]:= '!';

	beta := alpha;

	write(beta);
	writeln('*** - verify proper padding');
end.
