program testassign02(output);
{test lots of compiler warnings about assignments}
var 
	i,j:integer;
	a,b:boolean;
	arr:array[0..5] of integer;
begin
	writeln(i);
	j := ord(i);
	j := 9;
	writeln(j, i);
	arr[i] := 5;
	j := i;
	if i < j then writeln('less');
	if j < i then writeln('less');
	a := true;
	if a and b then writeln('and');
	if b or a then writeln('or');
	if (not b) then writeln('not');
	
end.	
