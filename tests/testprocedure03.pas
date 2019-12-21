program testprocedure03(output);
{tests local variables in procedures}
procedure foo(a,b:integer);
var q:integer;
begin
	q:=a*b;
	writeln(q);
end;

begin
	foo(6,7);
end.
