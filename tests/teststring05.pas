program teststring05(output);
{test printing string types}

type
	Length = 1..15;
	mystring = packed array[Length] of char;

var alpha:mystring;

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

	write(alpha);
	writeln('*** - verify proper padding');
end.
