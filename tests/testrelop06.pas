program testrelop06(output);
{relational operators with character types}

var c,d:char;

begin
	c := 'A';
	d := 'C';

	if c < d then
		writeln('A is less than C');

	if c = d then
		writeln('oops')
	else
		writeln('A is not equal to C');

	d := pred(pred(pred(d)));

	writeln ('d now equals ',d);

	if d < c then 
		writeln(d, ' is now less than ', c);

end.
