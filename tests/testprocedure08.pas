program testprocedure08(output);
{test procedures with no parameters}

var globalcount,i:integer;

procedure countup;
begin
	globalcount := globalcount + 1;
	writeln('countup has been called ', globalcount, ' times!');
end;

begin
	globalcount := 0;
	countup;
	writeln;
	for i := 27 to 34 do 
		countup;

end.
	
