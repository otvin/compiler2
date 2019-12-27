program compilefail19(output);
{parse failure - function missing colon between right paren and return type }

function addone(r:integer) integer ;
begin
	addone:=r+1;
end;

begin
	writeln(addone(3));
end.
