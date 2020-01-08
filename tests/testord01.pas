program testord01(output);
{tests basic use of ord function}

const letterq = 'q';

var mycharint:integer;mychar:char;mybool:boolean;myint:integer;

begin
	mycharint:=ord(letterq);
	writeln(mycharint);

	mychar:= 'F';
	writeln(ord(mychar));

	mybool:=True;
	writeln(ord(mybool));
	writeln(ord(not mybool));

	myint:= 32769;
	writeln(ord(myint));
	myint:= -30973;
	writeln(ord(myint));

end.
