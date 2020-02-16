program testwrite02(output);
{test explicit use of output in the write/writeln command}
begin
	write(output, 'hi');
	writeln(output, ' bye');
end.
