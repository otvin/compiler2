program compilefail66(output);
{invalid return type for a function}


type q = array[1..5] of boolean;
var myq:q;

function x(a:integer):q;
begin
	x[a] := true;
end;

begin
	myq := x(1);
end.
