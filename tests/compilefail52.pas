program compilefail52(output);
{function that does not return a value}

function addone(a:integer):integer;
var q:integer;
begin
	q:=a+1;
end;

begin
	writeln(addone(2));
end.
