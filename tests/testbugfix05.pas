program testbugfix05(output);
{Bug discovered Nov 8 2025.

Previous parsing of <simple-statement> missed <empty-statement>
}

begin

	repeat until true;
	while false do ;
	writeln('done');	
end.
