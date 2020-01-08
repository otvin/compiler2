program testchar03(output);
{test character passed byref}

procedure plusone(var c:char);
var i:integer;
begin
	i := ord(c);
	i := i + 1;
	c := chr(i);
end;

procedure printplusone(c:char);
var x:char;
begin
	x := c;
	writeln('before: ', x);	
	plusone(x);
	writeln('after: ', x);
end;

begin
	printplusone('0');
	printplusone('a');
	printplusone('%');
end.

	
