program compilefail10(output);
{missing a semicolon in the middle of the list of statements}
var i,j:integer;

begin
	i:=4;
	j:=7
	writeln(i+j);
end.
