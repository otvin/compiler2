program testfor02(output);
{for loop in a procedure}


procedure foo(j:integer);
var k:integer;
begin

	for k := 0 to j do begin
		writeln(k);
	end;
end;

begin

	foo(5);
	foo(2);
	foo(-7);
	foo(3);

end.
