program testarray03(output);

type
	subr = 1..10;
	arr = packed array[subr] of char;

var
	myarr:arr; 
	c:char;
	i:integer;

begin

	for i := 1 to 10 do begin
		myarr[i] := chr(96 + i);
	end;

	{someday we will be able to writeln packed arrays of char}
	for i := 1 to 10 do begin
		write(myarr[i]);
	end;

	writeln;

end.

	
