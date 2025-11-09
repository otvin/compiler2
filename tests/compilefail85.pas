program compilefail85(output);
{Test reuse of for control variable inside a for loop}
var a:integer;

begin
	for a := 1 to 5 do
		for a := 6 to 9 do
			writeln(a);
end.	
