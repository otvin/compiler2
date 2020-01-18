program compilefail55(output);
{should error when you do not assign the result of a function}
function oops(a:integer):integer;
begin
	a:=a+7;
	oops:=a*2;
end;

begin
	oops(3);
end.
