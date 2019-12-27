program testbyref05(output);
{simple test of passing byref parameters as actual parameters into a second function}

procedure l3(var a:integer; var a1:real; var a2:boolean);
begin
	a := a * 2;
	a1 := a1 * 2.0;
	a2 := False
end;

procedure l2(var b:integer; var b1:real; var b2:boolean);
begin
	l3(b, b1, b2);
end;

procedure l1(c:integer; c1:real);
var d:integer; d1:real; d2:boolean;
begin
	d := c + 2;
	d1 := c1 + 2.0;
	d2 := True;
	writeln(d, ' ', d1, ' ', d2);
	l2(d, d1, d2);
	writeln(d, ' ', d1, ' ', d2);
end;
begin
	l1(9,9.0);
end.

