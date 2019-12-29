program testsqrt01(output);
{tests square root and the error around trying to take square root of a negative number}

var q:real;

function half(r:real):real;
begin
	half := r/2;
end;

begin
	writeln(half(42.0));
	writeln(sqrt(42.0));
	q := 74.65;
	if q < 0 then
		writeln('oops!')
	else
		begin
			q := sqrt(q);
			writeln(q)
		end;
	writeln(sqrt(100));
	writeln(sqrt(-5.7));
end.
