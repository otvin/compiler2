program test(output);
{test that required functions that take integers will also work on subranges of integer type}
type
	q = 1..3;
var
	a : q;
begin
	a := 1;
	writeln(abs(a));
	writeln(odd(a));
end.	
