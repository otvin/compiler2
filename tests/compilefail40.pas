program compilefail40(output);
{cannot compare char and enumerated types with relops}

type car = (van, sedan, taxi, scooter);
	transport = car;

var c,d:char;q:transport;

begin
	c := 'A';
	d := 'C';
	q := sedan;
	

	if c > q then
		writeln('oops!');

end.
