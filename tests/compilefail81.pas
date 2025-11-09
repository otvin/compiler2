program compilefail81(output);
{ invalid structured type }
var
	a: packed char;
begin
	a := 'a';
	writeln(a);
end.
	
