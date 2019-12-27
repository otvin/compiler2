program compilefail13(output);
{undefined variable used as the lval of an assignment}
function one(a:integer):integer;
var i:integer;
begin
	one := a + 1;
end;

begin
	i:=one(7);
end.
