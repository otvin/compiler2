program compilefail83(output);
{pass a type definition instead of a boolean to an if statement}
type
	q = boolean;
begin
	if q then writeln('yes');
end.	
