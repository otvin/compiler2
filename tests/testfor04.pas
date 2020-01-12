program testfor04(output);
{overwriting the initial and final values will not change the number of iterations.  Example: Cooper p.29}


var a,b,Counter:integer;

begin
	writeln('should print ''Le plus ca change...'' 3 times');
	writeln('');

	a := 1;
	b := 3; 
	for Counter := a to b
		do begin
			writeln('Le plus ca change...');
			a := -2000;  {These assignments have no}
			B := 2001	 {effect on the for statement.}
		end
end.
