program testconst04(output);
{test maxint}

const negmax = -maxint;

var i:integer; 

begin
	i:=2147483640;

	repeat
		i:=i+1;
		writeln(i);
	until i = maxint;

	writeln('if I had gone any higher, I would have overflowed!');

	i:=-2147483640;

	repeat
		i:=i-1;
		writeln(i);
	until i = negmax;

	writeln('if I had gone any lower, I would have overflowed.  Or underflowed?');

end.
