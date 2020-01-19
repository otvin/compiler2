program testarray02(output);

type
	subr = 1..10;
	myarr = array[subr] of integer;

var
	arr:myarr;
	j:integer;

begin

	arr[5] := 7;
	arr[7] := 3;

	j := arr[5] + arr[7];

	writeln(j);

end.
