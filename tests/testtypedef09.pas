program testtypedef09(output);
{most typedefs are from Cooper p.99.  Tests subrange of an enumerated type.  Also tests passing in a subrange of an enumerated type
 into a procedure where the parameter is an alias for the host type of that enumerated type.}

type
	Color = (Red, Green, Blue, Orange);

	{this is mine}
	AnotherColor = Color;

	Positive = 1..maxint;
	TwoBits = -25..25;
	Index = 0..50;
	Primary = Red..Blue;
	ShortButLegal = 'A'..'A';
	Characters = 'a'..'z';

	{plus one of mine}
	AnotherShortButLegal = False..False;

var
	myothercolor:AnotherColor;
	someprimary:primary;

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

begin

	someprimary := Green;
	printcolor(someprimary);

	someprimary := succ(someprimary);
	printcolor(someprimary);

	if someprimary > Red then
		writeln('yes, it is greater than Red');

	if someprimary < Orange then
		writeln('yes it is less than orange');


	writeln('this should error:');
	someprimary := succ(someprimary);
	printcolor(someprimary);

end.
