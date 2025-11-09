program compilefail80(output);
{test non-ordinal type in array index}
var a:array[1..5] of integer;
begin
	a[1] := 4;
	writeln(a[1]);
	a[3.267] := 9;
end.

