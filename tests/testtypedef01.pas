program testtypedef01(output);
{test simple aliasing of types}

type
	a = integer;
	b = a;
	c = boolean;
	d = c;
	e = d;
	f = real;

var
	i:integer; j:a; k:b; l:e; m:f;

begin

	i := 1;
	j := 2;
	k := 3;
	l := True;
	m := 3.14;

	writeln(i);
	writeln(j);
	writeln(k);

	writeln(i + j, j + k, i + k);

	if l then
		writeln(m);
end.
