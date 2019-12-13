program testwhile03(output);
var x:integer;
begin
	x := 0;

	while x >= 1 do
		begin
			writeln('this should not execute');
			writeln('1/0');  {this will prevent an infinite loop by erroring}
		end;
	writeln('done');
end.
