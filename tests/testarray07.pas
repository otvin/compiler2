program testarray07(output);
{arrays with enumerated types as the subrange, then a range out of bounds}
type
	color2 = (red, blue, green, orange, pink);
	subcolor = blue..orange;
	myarray = array[subcolor] of integer;

var
	myarr:myarray;
	c:color2;
	i:integer;	

begin
	i := 10;

	for c := blue to orange do begin
		myarr[c] := i;
		i := i + 1;
	end;

	writeln(myarr[green]);

	writeln ('should see ok 3 times then an error');

	for c := orange downto red do begin
		myarr[c] := i;
		i := i + 1;
		writeln('ok');
	end;

	writeln('oops!');

end.


