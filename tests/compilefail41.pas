program compilefail41(output);
{test out of subrange assignment}

type
	myrange = 0..5;

var
	q:myrange;

begin

	q := 7;
	writeln(q);
end.
