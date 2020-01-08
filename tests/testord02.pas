program testord02(output);
{tests chr() - note that the compiler_test has issues reading the unprintable characters}

var i:integer;

begin

	i := 32;
	repeat
		writeln(i,': ',chr(i));
		i := i + 1;
	until i = 128;

	writeln('and this should fail with an error:');
	writeln(chr(256));

end.
