program testtypedef06(output);
{test subrange definition}

type
	myrange = 0..5;

var
	q:myrange;

begin

	q := 4;
	writeln(q);
	q := q + 1;
	writeln(q);
	writeln('and now we should fail with an error.');
	q := q + 1;

end.
