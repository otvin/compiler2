program testtypedef10(output);
{testing subranges when one of the identifiers is overridden in a proc}

type
	Color = (Red, Green, Blue, Orange);
	AnotherColor = Color;
	myrange = Red..Blue;

procedure printcolor(c:anothercolor);
begin
	if c = Red then
		writeln ('Red');
	if c = Green then
		writeln ('Green');
	if c = Blue then
		writeln ('Blue');
	if c = Orange then
		writeln ('Orange');
end;

procedure foo(i:integer);
var Blue:integer; q:myrange;
begin
	Blue := i;
	writeln(Blue);
	q := Red;
	printcolor(q);
	q := succ(q);
	printcolor(q);
	q := succ(q);
	printcolor(q);
	writeln('this should error');
	q := succ(q);
	printcolor(q);
end;

begin
	foo(3);
end.
