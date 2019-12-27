program compilefail16(output);
{type mismatch test - passing an int to a real variable parameter}

var i:integer;

procedure addone(var r:real);
begin
	r:=r+1.0;
end;

begin
	i:=7;
	addone(i);
end.
