program compilefail23(output);
{another missing identifier test}
var r:real;
procedure a(b:integer;c:real);
begin
	b := c + d;
	writeln(b);
end;

begin
	r := 9.7;
	a(3,r);
end.

