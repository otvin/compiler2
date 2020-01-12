program testmath07(output);
{test the odd() function}

var i:integer;

begin

	i := 2;
	if odd(i) then
		writeln('oops')
	else
		writeln('correct');

	
	if odd(i - 73) then
		writeln('correct')
	else
		writeln('oops');


	if odd(7*7+2) then
		writeln('correct')
	else
		writeln('oops');


	if odd(maxint) then
		writeln('correct')
	else
		writeln('oops');

end.
