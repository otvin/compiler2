program compilefail65(output);
{passing a constant identifier instead of a type identifier into the definition of an array}


const a = 3.14;

var b : array[a] of boolean;

begin
	b[1] := true;
	writeln(b[1]);
end.
