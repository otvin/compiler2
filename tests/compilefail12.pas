program compilefail12(output);
{semicolon missing after a procedure definition}
var i:integer;
function one(a:integer):integer;
begin
	one := a + 1;
end;

procedure two(var b:integer)	
begin
	b := b + 2;
end;

begin
	i := 7;
	two (i);
	writeln(one(i))	
end.
