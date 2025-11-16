program testarray24(output);
{Same test as testarray01 but with lexical alternatives (. and .) for the brackets}

type
	subr = 1..10;
	myarr = array(.subr.) of integer;

var
	arr:myarr;
	j:integer;

begin

	arr[5.) := 7;

	j := arr(.5];

	writeln(j);

end.
