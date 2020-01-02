program compilefail32(output);
{cannot assign to a constant}

const two=2;

procedure addtwo(a:integer);
const localtwo = two;
begin
	writeln(a + localtwo);
end;

begin
	two := 2;
	addtwo(17);
end.
