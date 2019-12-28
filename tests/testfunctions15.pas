program testfunctions15(output);
{call a function that updates a byref real parameter}

function squareit(r:real):real;
begin
	squareit := r * r;
end;

procedure forreal(var q:real);
begin
	q := squareit(q);
end;

procedure callit(p:real);
begin
	writeln(p);	
	forreal(p);
	writeln(p);
end;

begin
	callit(4.0);
end.
