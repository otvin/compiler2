program compilefail49(output);
{procedure call instead of function call to set initial value of the for statement}


var a,b,Counter:integer;

procedure threetimes(a:integer);
begin
	writeln(3 * a);
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
