program compilefail89(output);
{cannot 'not' a non-boolean}
var 
	i:integer;
	b:boolean;

begin
	i := 4;
	b := not i;
	writeln(b);
end.	
