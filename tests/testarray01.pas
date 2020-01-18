program testarray01(output);

type
	subr = 1..10;
	myarr = array[subr] of integer;

var
	arr:myarr;
	j:integer;

begin

	arr[5] := 7;

	j := arr[5];

	writeln(j);

end.
