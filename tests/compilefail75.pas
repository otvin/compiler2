program compilefail75(output);
{try to writeln() an array that isn't a string type}


var r:array[1..7] of boolean;


begin
	r[1] := true;
	writeln(r);
end.
