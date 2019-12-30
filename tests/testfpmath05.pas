program testfpmath05(output);


procedure writeit(r:real);
begin
	writeln(round(r));
	writeln(trunc(r));
end;

begin

	writeit(43.2);
	writeit(987.54);
	writeit(-234.23);
	writeit(-299.99);
end.
