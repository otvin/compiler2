program testconst03(output);
{define a local constant using a global constant}

const globaltwo = 2;

procedure addtwo(a:integer);
const localtwo = globaltwo;
begin
	writeln(a + localtwo);
end;

begin
	writeln('should print 19.');
	addtwo(17);
end.
