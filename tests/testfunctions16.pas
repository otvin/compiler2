program testfunctions16(output);
{test functions with no parameters}

var globalcount,i,j:integer;

procedure init;
begin
	globalcount := 0;
end;

function countup:integer;
begin
	globalcount := globalcount + 1;
	countup:=globalcount;
end;

begin
	init;
	j := countup;
	writeln(j);
	writeln;
	for i := 27 to 34 do 
		j := countup;
	writeln(j);	

end.
	
