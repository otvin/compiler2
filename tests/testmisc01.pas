program testmisc01(output);
begin
	{tests ensuring semicolon is a separator not a terminator.  Second statement does not
	have trailing semicolon.}
	write('hello ');
	writeln('world!')
end.
