program compilefail58(output);
{an array with index types of type a and b, should error if someone tries to reference it via [typeb, typea]}

type
	subrint = 1..10;
	subrchar = 'a'..'z';
	myarr = array [subrint] of array [subrchar] of boolean;

var
	i:integer;
	c:char;
	a:myarr;

begin

	i := 5;
	c := 'a';
	a[c, i] := True;

	write(a[c,i]);
end.
