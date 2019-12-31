program testfpmath07(output);


begin

	writeln('exp(1) = e: ',exp(1.0));
	writeln('exp(1) = e: ',exp(1));
	writeln('exp(-1) == 1/e = .3679: ',exp(-1.0));
	writeln('exp(2.469) = 11.8106: ',exp(2.469));
	writeln('exp(100.000001): 2.6881 * 10^43: ',exp(100.00001));
	writeln('exp(0.0023119): 1.002314: ',exp(0.0023119));

end.
