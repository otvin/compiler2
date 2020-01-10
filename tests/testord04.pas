program testord04(output);
{passing enumerated constant into pred() and succ()}

type car = (van, sedan, taxi, scooter);
	transport = car;

var q:transport;

begin
	q := succ(sedan);

	if q > van then
		writeln('yes!');

	q := pred(taxi);

	if q < taxi then
		writeln('yes!');

end.
