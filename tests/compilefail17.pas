program compilefail17(output);
{type mismatch test - assigning real return value from a function to an int}

var i:integer;j:integer;

function addone(r:integer):real;
begin
	addone:=r+1.0;
end;

begin
	i:=7;
	j:=addone(i);
	writeln(j);
end.
