program testarray23(output);
{test local variable arrays}

type myarr=array[-5..5] of boolean;

var
	a:myarr;
	i:integer;

procedure printarr(d:myarr);
var i:integer;
begin
	i := -5;
	while i <=5 do begin
		write(d[i], ' ');
		i := i + 1;
	end;
	writeln;
end;

procedure invertarr(b:myarr);
var
	i:integer; c:myarr;
begin
	i := -5;
	while i <= 5 do begin
		c[-1 * i] := b[i];
		i := i + 1;
	end;
	printarr(b);
	writeln('inverted');
	printarr(c);
end;

begin
	i := -5;
	while i <= 5 do begin
		a[i] := (i < -3) or (i = 1);
		i := i + 1;
	end;
	invertarr(a);
end.
