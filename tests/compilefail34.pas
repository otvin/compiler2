program compilefail34(output);
{cannot sign a boolean constant}

const 
	myfalse = -True;

begin

	if myfalse then
		writeln('myfalse is true');
	else
		writeln('myfalse in false');

end.
