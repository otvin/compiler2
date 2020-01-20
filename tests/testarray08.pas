program testarray08(output);
{test array bounds check failure on the high side of the subrange}

type
	myarr = array [-7..31] of char;

var
	c:char; i:integer; a:myarr;

begin

	c := 'A';
	writeln('you should get an error after lower case g.');
	for i := -7 to 32 do begin
		a[i] := c;
		c := succ(c);
		write(a[i]);
	end;
end.
