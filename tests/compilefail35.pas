program compilefail35(output);
{cannot sign a string constant}

const 
	mystring = -'four';

begin

	writeln(mystring);

end.
