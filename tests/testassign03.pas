program testassign03(output);
{compile warning about assignment to the control variable of a for loop after the loop ends}
var 
	i:integer;
begin
	for i:= 1 to 3 do writeln(i);
	
	i := i + 1;
	writeln(i);	
end.	
