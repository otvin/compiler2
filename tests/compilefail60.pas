program compilefail60(output);
{another assignment compatibility test for value parameters}


procedure printint(a:integer);
begin
	writeln(a);
end;

begin
	printint(3.78);
end.
