program testprocedure04(output);
{tests scope rules for global vs. local variables in procedures}
var i:integer;
procedure overridescope(a:integer);
var i:integer;
begin
	i:=a+7;
	writeln(i);
end;
procedure accessglobal(a:integer);
var b:integer;
begin
	b:=a*i;
	writeln(b);
end;
procedure overrideinparameter(i:integer);
var b:integer;
begin
	b:=i*9;
	writeln(b);
end;
begin
	i:=987;
	write('should be 10: ');
	overridescope(3);

	write('should be -5922: ');
	accessglobal(-6);

	write('should be 63: ');
	overrideinparameter(7);
end.
