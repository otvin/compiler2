program compilefail14(output);
{cannot pass a procedure result in as the value to a system function (writeln)}
var i:integer;

procedure two(var b:integer);	
begin
	b := b + 2;
end;

begin
	writeln(two(7));
end.
