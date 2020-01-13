program testfunctions17(output);
{test some sample functions from Cooper p.77-78}

var myseed,i:integer;

function Tan(Angle: real): real;
{returns the tangent of its argument.}
begin
	Tan := sin(Angle) / cos(Angle)
end;

function Even (Number: integer): boolean;
begin
	Even := (Number mod 2) = 0
	{We could have just said Even := not odd(Number).}
end;

function Random(var Seed: integer): real;
{returns a pseudo-random number such that 0 <= Random(Seed) < 1}
const Modulus = 65536;
	Multiplier = 25173;
	Increment = 13849;
begin
	Seed := ((Multiplier*Seed) + Increment) mod Modulus;
	Random := Seed/Modulus
end;


function GreatestCommonDenominator(i,j:integer):integer;
	{returns the greatest common denominator of i and j.}
begin
	if i < j
		then GreatestCommonDenominator := GreatestCommonDenominator(j,i)
	else if j=0
		then GreatestCommonDenominator := i
		else GreatestCommonDenominator := GreatestCommonDenominator(j, i mod j)
end;

begin

	writeln('GCD of 8 and 12 should be 4: ', GreatestCommonDenominator(8,12));
	writeln('GCD of 60 and 90 should be 30: ', GreatestCommonDenominator(60,90));
	writeln('GCD 84723912 and 999331 should be 1 since 999331 is prime: ', GreatestCommonDenominator(84723912, 999331));

	writeln('Is 48 even? ', Even(48));
	writeln('Is -932 even? ', Even(-932));
	writeln('Is 38121 even? ', Even(38121));

	writeln('Tangent of Pi should be 0: ', Tan(3.14159));
	writeln('Tangent of Pi/12 should be 0.267949...: ', Tan(3.14159/12));
	writeln('Tangent of 16 Pi / 13 should be 0.885922...: ', Tan(16 * 3.14159 / 13));

	
	myseed := 30973;
	writeln ('and now for some pseudo-random numbers');
	for i := 0 to 10 do begin
		writeln(Random(myseed));
	end;
		
end.


