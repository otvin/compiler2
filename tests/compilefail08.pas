program compilefail08(output);
{validates that a local variable named the same as a parameter into a function is properly detected}
function oops(a:integer):integer;
var
	a:real;
begin
	a:=a+7;
	oops:=a*2;
end;

begin
	oops(3);
end.
