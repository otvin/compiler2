program testtypedef01(output);
{test nested type definitions, including redefinition of types}

type
	myint=integer;
	otherint=myint;
	changes=myint;

var
	i:changes;

procedure myproc(a:integer);

	type 
		myreal=real;
		changes=myreal;

	var 
		j:changes;

	begin
		j := i + a;
		writeln('this should be floating point 3: ', j);
	end;

begin

	i := 1;
	myproc(2);

end.
