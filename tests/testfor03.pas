program testfor03(output);
{test nested for loops}

var i,j:integer;

begin

	for i := 0 to 10 do 
		begin
		for j := 0 to i do
			begin
				writeln(j, ' * ', i, ' = ', j*i);
			end;
		end;

end.
