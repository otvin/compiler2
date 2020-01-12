program compilefail46(output);
{reals as control variable in a for loop}

type fruit = (apple,banana,cherry,peach,mango);
var i:integer;

procedure foo(j:integer);
var k:real;
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
