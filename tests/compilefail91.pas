program compilefail91(output);
(* test invalid real number format *)
var r:real;
begin
	r := 3.1415eq-03;
	writeln(r);
end.
