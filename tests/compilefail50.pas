program compilefail50(output);
{procedure call instead of function call to set final value of the for statement}


var a,b,Counter:integer;

function threetimes(a:integer):integer;
begin
	threetimes := 3*a;
end;

procedure sixtimes(a:integer);
begin
	writeln(6*a);
end;

begin
	b := 7;

	for a := threetimes(b) to sixtimes(b) do 
		begin
			writeln(a);
		end;	

end.
