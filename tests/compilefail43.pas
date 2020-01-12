program compilefail43(output);
{illegal use of global variable as the control variable of a for statement}

var i:integer;

procedure foo(j:integer);
var k:integer;
begin

	for k := 0 to j do begin
		writeln(k);
	end;

	for i := 15 downto j do begin
		writeln(i);
	end;
end;

begin

	foo(5);
	foo(2);
	foo(-7);
	foo(3);

end.
