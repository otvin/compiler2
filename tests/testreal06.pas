program testreal06(output);
var negpi:Real; negpiInt:Integer;
function realfunc(a:Real):Real;
begin
    realfunc:=a*negpi;
end;

function intfunc(a:Integer):Integer;
begin
    intfunc:=a*negpiInt;
end;

begin
    negpi := -3.14159265358979323846264338;
    negpiInt := -3;
    writeln(realfunc(1.0));
    writeln(intfunc(1));
end.
