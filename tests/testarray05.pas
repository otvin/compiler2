program testarray05(output);
{multi-dimensional arrays}

type
	multidarray = array[1..10, 1..7] of integer;

var
	myarr:multidarray;
	i,j:integer;

begin

	myarr[3][5] := 15;
	myarr[4,7] := 28;

	writeln(myarr[3,5] * myarr[4][7]);
	writeln;

	for i := 1 to 10 do begin
		myarr[i,1] := i;
		myarr[i,2] := 2*i;
	end;

	writeln(myarr[7,1] * myarr[6][2]);

	for i := 1 to 10 do begin
		for j := 3 to 4 do begin
			myarr[i,j] := i *j;
		end;
	end;

	write(myarr[5][4], ' ');

	writeln(myarr[6,3]);
	

	for j := 1 to 4 do begin
		writeln(myarr[3][j]);
	end;

	for i := 2 to 3 do begin
		for j := 2 to 3 do begin
			write(myarr[i][j], ' ');
		end;
	end;

	writeln;

end.
