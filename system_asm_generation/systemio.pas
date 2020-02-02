program systemio(output);
{This file is used to generate the assembly that goes into the file compiler2_system_io.asm.  

To use:
	1) compile this file via
		python3 compiler.py systemio.pas

	2) open systemio.asm and then grab the "printstringtype" procedure.

	3) past that into compiler2_system_io.asm.  Edit the labels so that they will be
	   globally unique.

	4) remove the bounds-checking code.

}

type
	Length = 1..10;
	mystring = packed array[Length] of char;

var alpha:mystring;

procedure printstringtype(s:mystring; k:integer);
var i:integer;
begin
	i := 1;
	while i <= k do begin
		if ord(s[i]) = 0 then 
			write(' ')
		else
			write(s[i]);

		i := i + 1;
	end;
end;



begin
	alpha[1] := 'H';
	alpha[2] := 'e';
	alpha[3] := 'l';
	alpha[4] := 'l';
	alpha[5] := 'o';
	alpha[6] := '!';

	printstringtype(alpha, 10);
	writeln;
end.


