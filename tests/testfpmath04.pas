program testfpmath04(output);
begin
	writeln(sqr(0.01));
	writeln(sqr(-0.0001));
	writeln(sqr(1.0));
	writeln(sqr(-10.0));
	writeln(sqr(sqr(sqr(100000000000.00))));
	writeln(sqr(-3.14159));
	writeln(sqr(sqr(sqr(sqr(99988877776665551287982173981273981732.123123)))));
end.
