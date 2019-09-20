program testrelop04(output);
var
	a,b,c,d:Real;
begin
	a:=3.72;
	b:=a;
	c:=a*b;

	if a = b then
		writeln('equal');

	b:=3.72;

	if b = a then
		writeln('equal');

	if c <> a then
		writeln('not equal');

	if c < a then
		writeln('OOPS!!!')
	else
		writeln('not less than');

	if b >= a then
		writeln('greater or equal');

	if c >= a then
		writeln('greater or equal');

	if a >= c then
		writeln('OOPS!!!')
	else
		writeln('not greater or equal');

end.

