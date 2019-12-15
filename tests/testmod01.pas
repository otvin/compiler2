program testmod01(output);
begin
	writeln('Should be 19: ', 131962 mod 309);
	{because mod takes precedence over the unary minus, this is read
	-1 * (23373077 mod 727)}	
	writeln('Should be -27: ',-23373077 mod 727);
	{this forces the mod to be of a negative number, testing 6.7.2.2 of the iso standard}
	writeln('Should be 1: ', (-5) mod 2);
end.
