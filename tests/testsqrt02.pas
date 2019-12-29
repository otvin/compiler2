program testsqrt02(output);

procedure quadraticformula(a,b,c:real);

	{input: the coeffients for a parabola ax^2 + bx + c
     prints out the roots}

var discriminant, axisofsymmetry:real; isimaginary:boolean;
begin

	axisofsymmetry := (-1 * b) / (2 * a);
	discriminant := (b * b) - (4 * a * c);	

	if discriminant < 0 then
		begin
			discriminant := -1 * discriminant;
			discriminant := sqrt(discriminant);
			writeln('root 1: x = ', axisofsymmetry, ' + ', discriminant / (2 * a), 'i');
			writeln('root 2: x = ', axisofsymmetry, ' - ', discriminant / (2 * a), 'i')
		end
	else 
		begin
			discriminant := sqrt(discriminant);
			writeln('root 1: x = ', axisofsymmetry + (discriminant / (2 * a)));
			writeln('root 2: x = ', axisofsymmetry - (discriminant / (2 * a)))

		end
end;

begin

	quadraticformula(9,3,-14);
	quadraticformula(2,37,-4);
	quadraticformula(3.9,-19.6,0.1);
	quadraticformula(1,1,1);
end.
