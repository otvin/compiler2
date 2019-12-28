program compilefail22(output);
{another missing identifier test}
var r:real;
procedure a(b:integer;c:real);
begin
	d := c + b;
	writeln(d);
end;

begin
	r := 9.7;
	a(3,r);
end.

