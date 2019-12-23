program testlocalvar02(output);

function addsquares(one : Integer; two: Integer) : Integer;
var localvar, localvar2 : Integer;

begin
    localvar := one * one;
    localvar2 := two * two;
    addsquares := localvar + localvar2

end;


begin

    writeln('3^2 plus 4^2 should be 25');
    writeln(addsquares(3,4));

    writeln('(8*6)^2 plus (7*7)^2 should be 4705');
    writeln(addsquares((8*6), (7*7)));

    writeln('-4^2 and 0^2 should be 16');
    writeln(addsquares(-4,0))

end.
