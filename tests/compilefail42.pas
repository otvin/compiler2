program compilefail42(output);
{illegal assignment to the control variable of a for statement}

var i:integer;

begin

	for i := 1 to 7 do
		begin
			writeln(i);
			i := i + 2;
		end;

end.
