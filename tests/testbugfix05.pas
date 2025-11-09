program testbugfix05(output);
{Bug discovered Nov 8 2025.

Previous parsing of <simple-statement> missed <empty-statement>
}
var i:integer;
begin

	repeat until true;
	while false do ;
	for i := 1 to 2 do ;
	writeln('done');	
end.
