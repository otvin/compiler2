program compilefail53(output);
{can't have a const that has a sign in front of an enumerated type value}

type
	car = (Chevy, Ford, Dodge);

procedure foo;
const mycar = -Ford;
begin
	writeln('hi');
end;


begin
	foo;
end.
	
