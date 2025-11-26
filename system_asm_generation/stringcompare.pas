program stringcompare(output);
{This file is used to generate the assembly that goes into the file compiler2_stringcompare.asm.  

To use:
	1) compile this file via
		python3 compiler.py stringcompare.pas

	2) open stringcompare.asm and then grab the "stringcompare" procedure.

	3) paste that into compiler2_stringcompare.asm.  Edit the labels so that they will be
	   globally unique and rename function to _PASCAL_STRING_COMPARE

	4) remove the bounds-checking code.

}

type
	Length = 1..10;
	mystring = packed array[Length] of char;

var alpha,beta:mystring;

function stringcompare(s:mystring; t:mystring; k:integer):integer;
var i:integer; ret:integer;
begin
	i := 1;
	ret := 0;
	while (i <= k) and (ret=0) do begin
		if s[i] < t[i] then
			ret := -1
		else if s[i] > t [i] then
			ret := 1;
		i := i + 1;
	end;
	stringcompare := ret;
end;




begin
	alpha[1] := 'H';
	alpha[2] := 'e';
	alpha[3] := 'l';
	alpha[4] := 'l';
	alpha[5] := 'o';
	alpha[6] := '!';

	beta := alpha;

	if stringcompare(alpha, beta, 10) = 0 then 
		writeln('equal!');
end.
