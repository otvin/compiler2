program testfpmath02(output);
var i,j,pi,twopi, mysin,mycos:real;

procedure printApproxNspaces(n:real);
var r:real;
begin
	r := 0;

	while r < n do
		begin
			write (' ');
			r := r + 1.0;
		end;
end;

begin

	{would be much better to write this with a for loop and trunc but haven't 
	 built those into the compiler yet}

	pi := 3.1415926535;	
	twopi := 2 * pi;

	i := -1 * twopi;

	while i <= twopi do
		begin
			mysin := sin(i);
			mysin := (mysin * 40.0) + 40.0;
			printApproxNSpaces(mysin);
			writeln('*');
			i := i + 0.1;
		end;

	writeln('');
	writeln('');
	
	i := -1 * twopi;

	while i <= twopi do
		begin
			mycos := cos(i);
			mycos := (mycos * 40.0) + 40.0;
			printApproxNSpaces(mycos);
			writeln('*');
			i := i + 0.1;
		end;

end.
			


	

