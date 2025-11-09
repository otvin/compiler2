program compilefail79(output);
{invalid character}
var
	a:boolean;
begin
	writeln('hi');
	a := !true;
	writeln(a);
end.
