program testfunctions13(output);
{tests boolean return values from functions}

function isless(a,b:integer):boolean;
begin
	if a < b then
		isless := True
	else
		isless := False
end;

function isgreater(a,b:real):boolean;
begin
	if a > b then
		isgreater := True
	else
		isgreater := False
end;

begin
	write('should be true: ');
	writeln(isless(3,7));
	write('should be false: ');
	writeln(isless(-19,-282));
	writeln('should be true: ', isgreater(7.5,-2.5), ' then false: ', isgreater(19,28.99));
end.
