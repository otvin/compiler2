program testtypedef07(output);
{test subrange definition with characters}

type
	uppercase = 'A'..'Z';

var
	q:uppercase;

begin

	q := 'T';
	writeln(q);
	q := succ(q);
	writeln(q);
	q := succ(q);
	writeln(q);
	q := succ(q);
	writeln(q);
	q := succ(q);
	writeln(q);
	q := succ(q);
	writeln(q);
	q := succ(q);
	writeln(q);	
	writeln('and now we should fail with an error.');
	q := succ(q);
	writeln(q);
end.
