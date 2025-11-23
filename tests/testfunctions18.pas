program testfunctions18(output);
{Test a function that sometimes returns a value and other times does not, triggering runtime error.}

function myfunc(a:integer) : Integer;
var b:boolean;
begin
    if a < 0 then myfunc:=-1;
    if a > 5 then myfunc:=5;
end;

begin
	writeln(myfunc(-1));
	writeln(myfunc(1));  (* should fail *)
	writeln(myfunc(7));
end.s
