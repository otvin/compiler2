program testboolean01(output);
var
	a,b:boolean;
begin
	a:=true;	
	writeln(a);
	b:=FAlse;  {test case-insensitivity of the token "false"}
	writeln(b);
	writeln('True: ',a,' False: ',b);
end.
