program testfor05(output);
{using functions to set the initial and final values of the for statement}


var a,b,Counter:integer;

function threetimes(a:integer):integer;
begin
	threetimes := 3 * a;
end;

function sixtimes(a:integer):integer;
begin
	sixtimes := 6 * a;
end;

begin
	b := 7;

	for a := threetimes(b) to sixtimes(b) do 
		begin
			writeln(a);
		end;	

end.
