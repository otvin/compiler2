program testtypedef08(output);
{math with subrange types}

type
	myrange = -10..10;

var
	q:myrange;

begin

	q := 2;
	writeln(q);
	q := q * (-2);
	writeln(q);
	q := q * (-2);
	writeln(q);	
	writeln('and this should error...');
	q := q * (-2);

end.
