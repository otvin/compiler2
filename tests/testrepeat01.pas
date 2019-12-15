program testrepeat01(output);
var
	i:integer;
begin
	i:=10;
	repeat
		writeln(i);
		i:=i-1;
	until i=0;
	writeln('done');
end.
