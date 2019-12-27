program compilefail09(output);
{validates that mulitple parameters with same name in a function generates an error}
function oops(a:integer; b: boolean; a:real):integer;
var
	q:real;
begin
	q:=a+7;
	oops:=q*2;
end;

begin
	oops(3, True, 4.7);
end.
