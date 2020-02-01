program testarray18(output);
{array as variable parameter to procedure}

type myarr = array [1..5] of integer;

var a: myarr; i:integer;

procedure initarr(var z:myarr);
var i:integer;
begin
	i := 1;
	while i <= 5 do begin
		z[i] := i * i;
		i := i + 1;
	end;
end;


begin

	initarr(a);
	i := 1;
	while i <= 5 do begin
		writeln(a[i]);
		i := i + 1;
	end;
end.
