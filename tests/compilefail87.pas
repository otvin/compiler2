program compilefail87(output);
{cannot use boolean type in math}
var 
	i:integer;
	b:boolean;

begin
	b := true;
	i := 1 + b;
	writeln(i);
end.	
