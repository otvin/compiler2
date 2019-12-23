program testlocalvar01(output);

var
    globalOne : Integer;
    globalTwo : Integer;

function alpha(paramOne:Integer; paramTwo:Integer) : Integer;
var
        localOne : Integer;
        localTwo : Integer;
begin
        localOne := paramOne;
        localTwo := paramTwo;
        alpha := localOne + localTwo
end;


begin

    writeln(alpha(4,7))

end.
