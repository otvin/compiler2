program testprocedure09(output);
{ tests empty statement inside procedure}
var i:integer;
procedure foo(a:integer);
begin
end;

begin
	i:=7;
	foo(i);
	foo(14);
	writeln(i);
end.
