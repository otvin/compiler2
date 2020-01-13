program compilefail51(output);
{test procedures that try to set a return value}

var i:integer;

procedure addone(var a:integer);
begin
	a := a + 1;
	addone := a;
end;

begin
	i := 0;
	addone(i);
	writeln(i);
end.
