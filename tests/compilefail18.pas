program compilefail18(output);
{parse failure - function missing return type}

function addone(r:integer);
begin
	addone:=r+1;
end;

begin
	writeln(addone(3));
end.
