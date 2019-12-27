program compilefail11(output);
{cannot pass a procedure result in as the value to a function}
var i:integer;
function one(a:integer):integer;
var i:integer;
begin
	one := a + 1;
end;

procedure two(var b:integer);	
begin
	b := b + 2;
end;

begin
	i:=one(two(7));
end.
