program testconst01(output);
const 
	consti = 3;
	negi = -consti;
	neg4 = -4; 
	pi = 3.14;
	pluspi = +3.14;
	negpi = -pi;
	alsopi = -negpi;
	myname = 'Fred';
	someconst = True;
	otherconst = False;
var j:integer;
begin
	
	j := consti + 2;
	writeln('A constant of 3 plus a literal of 2, assigned to a variable, equals: ', j);
	writeln('2 pi equals: ', 2 * pi);
	writeln('My name is ', myname);
	if someconst then
		writeln('Successful test with constant: ', someconst);

	if otherconst then
		writeln('Oops - this should not be seen.')
	else
		writeln('Successful test with constant: ', otherconst);

	writeln('4 times double-negative pi equals: ', 4.0 * alsopi);

	writeln('Negative pi equals: ', negpi);
	writeln('Plus pi equals: ', pluspi);
	writeln('Should be neg 3: ', negi);
	writeln('Should be neg 4: ', neg4);

	
end.
