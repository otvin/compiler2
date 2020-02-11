program testtypedef13(output);
{test boolean operations with a variable of type integer subrange}

type q = 1..10;
var a,b:q;

begin
	a := 3;
	b := 5;

	if (a<b) then writeln('yes!');
end.
