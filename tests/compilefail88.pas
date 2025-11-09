program compilefail88(output);
{cannot use reals in idiv}
var 
	i:integer;
	r:real;

begin
	r := 31.41;
	i := r div 5;
	writeln(i);
end.	
