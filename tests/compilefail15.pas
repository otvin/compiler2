program compilefail15(output);
{test passing a literal as a variable parameter}

var i:integer;

procedure addone(var a:integer);
begin
	a:=a+1;
end;

begin
	i:=7;
	addone(i);
	addone(7);
end.
