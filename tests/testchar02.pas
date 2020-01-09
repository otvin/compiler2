program testchar02(output);
{test a function that accepts and returns char}

var
	c:char;

function identity(mychar:char):char;
begin
	identity:=mychar;
end;

begin
	c:='a';

	writeln(identity('X'));
	writeln(identity(c));
end.
