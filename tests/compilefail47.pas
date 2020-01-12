program testfor03(output);
{test assigning to outer for loop control variable in an inner for loop}

var i,j:integer;

begin

	for i := 0 to 10 do 
		begin
		for j := 0 to i do
			begin
				i := 0;				
				writeln(j, ' * ', i, ' = ', j*i);
			end;
		end;

end.
