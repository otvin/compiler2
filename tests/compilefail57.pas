program compilefail57(output);
{test reference outside of array bound, to the greater than side}

type myarray = array[1..9,2..12] of char;
var myarr:myarray;

begin

	myarr[1,8] := 'a';  {should work}
	myarr[4,13] := 'z';  {should compile error}

	writeln(myarr[1,8]);
end.
