program testscope01(output);
var
    one : Integer;
    two : Integer;

function addsquares(one : Integer; two: Integer) : Integer;
var localvar : Integer;
    localvar2 : Integer;

begin
    localvar := one * one;
    localvar2 := two * two;
    {scope rule test - verifying that we do not assign to the global variable of same name}
    two := 9876;
    addsquares := localvar + localvar2

end;

function justadd(one : Integer; other: Integer) : Integer;
begin
    justadd := one + other;
    {scope rule test - verifying that this DOES assign to global variable}
    two := 17
end;

begin

    two := 42;
    writeln('3^2 plus 4^2 should be 25');
    writeln(addsquares(3,4));

    writeln('Should be 42:');
    writeln(two);

    writeln('(8*6)^2 plus (7*7)^2 should be 4705');
    writeln(addsquares((8*6), (7*7)));

    writeln('8 + 7 = 15');
    writeln(justadd(8,7));

    writeln('Should be 17:');
    writeln(two);

    writeln('-4^2 and 0^2 should be 16');
    writeln(addsquares(-4,0))

end.
