program compilefail56(output);
{test reference outside of array bound, to the less than side}

type myarray = array[-4..19] of char;
var myarr:myarray;

begin

	myarr[-4] := 'a';  {should work}
	myarr[-5] := 'z';  {should compile error}

	writeln(myarr[-4]);
end.
