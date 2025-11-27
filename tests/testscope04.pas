program testscope04(output);
{test overriding required identifiers.}
var succ:real; ln:integer; 
begin
	ln := 4;
	succ := pred(ln);
	writeln('Should be 3.0');
	writeln(succ);
end.
	
