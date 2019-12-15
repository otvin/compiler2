program compilefail05(output);
var
	i:integer;
begin
	i:=10;
	repeat
		writeln(i);
		{this should be an assignment, not a straight equals}
		i=i-1;
	until i=0;
	writeln('done');
end.
