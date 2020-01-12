program testord05(output);
{test pred() and succ() with char types}

var c:char;

begin

	c := 'A';

	writeln(c);

	c := pred(c);
	writeln(c);

	c := pred(c);
	writeln(c);

	c := 'g';

	c := succ(c);
	writeln(c);

	c := succ(c);
	writeln(c);

	c := chr(3);
	c := pred(c);  { c = chr(2) }
	c := pred(c);  { c = chr(1) }
	writeln('should be ok');
	c := pred(c);  { c = chr(0) }
	writeln('next line should error');
	c := pred(c);

end.
