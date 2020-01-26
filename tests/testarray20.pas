program testarray19(output);
{array as byval parameter to procedure, not as the first parameter}

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


procedure printmultarray(a,b:integer; q:myarr);
{prints the array with some math added to make sure rsi, rdi were protected properly}
var i:integer;
begin
	i := 1;
	while i <= 5 do begin
		writeln((a * q[i]) + b);
		i := i + 1;
	end;
end;

procedure printarray(q:myarr);
var i:integer;
begin
	i := 1;
	while i <= 5 do begin
		writeln(q[i]);
		i := i + 1;
	end;
end;

begin

	initarr(a);
	printarray(a);
	printmultarray(3,9,a);
end.
