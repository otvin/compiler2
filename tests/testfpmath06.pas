program testfpmath06(output);


begin

	writeln('ln(1) = 0: ', ln(1));
	writeln('ln(10) = 2.3026: ', ln(10));
	writeln('ln(3.718) = 1.3132: ', ln(3.718));
	writeln('ln(98765.432) = 11.5005: ', ln(98765.432));
	writeln('next line should error');
	writeln(ln(0));

end.
