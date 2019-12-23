program testprocedure06(output);
{test real and boolean parameter values in procedures}
{test large number of parameters to procedures}
procedure whichone(a:integer; b:real; c:boolean);
begin
	if c then
		begin
			writeln(a);
		end
	else
		writeln(b);
end;

procedure moreparams(a,b:integer; r,s,t: real; c,d:boolean; e:integer);
begin
	if c then
		writeln(a*b)
	else
		writeln(r*s);

	if d then
		writeln(a+b+e)
	else
		begin
			writeln(t + s);
			writeln(t / r);
		end
end;

begin
	write('should be 9: ');
	whichone(9,3.9,True);
	write('should be 3.9: ');
	whichone(9,3.9,False);

	writeln('should print -27, 8.2, 3.629');
	moreparams(9, -3, 2.7, -1.6, 9.8, True, False, -4);
	writeln('should print -4.32, 2');
	moreparams(9, -3, 2.7, -1.6, 9.8, False, True, -4);

end.
