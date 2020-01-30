program testconst06(output);
{constants of enumerated types}

type cars = (buick, ferrari, mgb, lexus);

procedure isbest(c:cars);
const bestcar = ferrari;
begin
	if c = bestcar then
		writeln('YES!')
	else
		writeln('No!');
end;

begin
	isbest(buick);
	isbest(ferrari);
	isbest(mgb);
	isbest(lexus);
end.
