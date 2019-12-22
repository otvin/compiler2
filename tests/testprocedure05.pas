program testprocedure05(output);
{test passing parameters of multiple types to procedures, validating stack alignment
 before calling printf}
procedure foo(r: real; a:integer);
begin
	if a < r then
		writeln(r)
	else
		writeln(a)
end;
begin
	foo(-1.6,1);
	foo(1.6,-1);
end.
