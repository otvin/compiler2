program testarray10(output);


var
	myarray:array[1..10] of real;
	i:integer;

begin

	myarray[1] := 1.1;
	myarray[2] := 1.1;
	for i := 3 to 10 do begin
		myarray[i] := myarray[i-1] + myarray[i-2];
	end;

	for i := 1 to 10 do begin
		writeln(myarray[i]);
	end;
end.
