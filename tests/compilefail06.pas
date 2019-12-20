program compilefail06(output);
procedure mac(a,b:integer);
	begin
		writeln(a);
		writeln(b);
	end;
function add(c,d:real):real;
	begin
		add:=c+d;
	end;
begin
	{should get an error here about invalid number of parameters}	
	mac(4);
	writeln(add(4.0,7.5));
end.
