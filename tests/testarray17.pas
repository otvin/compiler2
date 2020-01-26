program testarray17(output);
{complex array assignment}

type myarr = array [1..5] of integer;
	 bigarr = array [1..3] of myarr;

var a: myarr;
	b: bigarr;
	i: integer;

begin
	i := 1;
	while i <= 5 do begin
		a[i] := i;
		i := i + 1;
	end;

	b[1] := a;

	i := 1;
	while i <= 5 do begin
		writeln(b[1,i]);
		i := i + 1;
	end;
end.
