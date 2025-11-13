program testfpmath09(output);
var i:integer;
begin
	(* Previously we were computing exp(x) correctly for some but not all x *)
	for i := 0 to 20 do
		writeln(exp(i));
		
	writeln('');
	writeln(exp(-1.2345));
	writeln(exp(3.0973));
   
end.
