program testord06(output);
{succ() overflow with char types}

var c:char;

begin



	c := chr(253);
	c := succ(c);  { c = chr(254) }
	writeln('should be ok');
	c := succ(c);  { c = chr(255) }
	writeln('next line should error');
	c := succ(c);

end.
