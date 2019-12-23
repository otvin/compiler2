program testfunctions01(output);
var
    a:Integer;
    b:Integer;

function myfunc(n : Integer) : Integer;
begin
    myfunc := n+1
end;

begin

    a := 0;
    b := myfunc(a);
    writeln('Should be 1');
    writeln(b)

end.
