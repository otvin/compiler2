program testarray16(output);
{basic array assignment}

type myarr = array [1..5] of integer;

var a,b:myarr;
	i: integer;

begin
	i := 1;
	while i <= 5 do begin
		a[i] := i;
		i := i + 1;
	end;

	b := a;

	i := 1;
	while i <= 5 do begin
		writeln(b[i]);
		i := i + 1;
	end;
end.
