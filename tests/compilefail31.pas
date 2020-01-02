program compilefail31(output);
{cannot define a constant using a variable}

{32 is can't assign to a constant}

var globaltwo:integer;

procedure addtwo(a:integer);
const localtwo = globaltwo;
begin
	writeln(a + localtwo);
end;

begin
	globaltwo := 2;
	addtwo(17);
end.
