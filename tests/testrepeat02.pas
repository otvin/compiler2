program testrepeat02(output);
var
	i:integer;
begin
	i:=10;
	repeat
		writeln(i);
		i:=i-1;
	until i<=10;  {shows that it executes at least once}
	writeln('done');
end.
