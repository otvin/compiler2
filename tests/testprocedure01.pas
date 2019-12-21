program testprocedure01(output);
var i:integer;
procedure foo(a:integer);
begin
	writeln(a);
end;

begin
	i:=7;
	foo(i);
	foo(14);
end.
