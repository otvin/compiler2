program testarray06(output);
{multi-dimensional arrays}

type
	multidarray = array[1..10, 1..7] of integer;

var
	
	myarr:multidarray;
	i,j,k:integer;	

begin

	for i := 1 to 10 do begin
		for j := 1 to 7 do begin
			myarr[i][j] := maxint;
		end;
	end;

	for j := 1 to 7 do begin
		for i := 1 to 10 do begin
			write(myarr[i,j], ' ');
		end;
		writeln;
	end;

	writeln(myarr[7,4]);
	writeln(myarr[4,5]);

end.
