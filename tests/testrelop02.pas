program testrelop02(output);
{tests real functions, but more importantly, tests real relops}
var
    onevar: Real;
    othervar: Real;

function myLessThan(a:Real; b:Real):Integer;
begin
    if a < b then
        myLessThan := 1
    else
        myLessThan := 0
end;

function myGreaterThan(a: Real; b: Real):Integer;
begin
    if a > b then
        myGreaterThan:= 1
    else begin
        myGreaterThan:= 0;
    end;
end;


begin

    if 1.1 < 2.1 then
        writeln('1.1 is less than 2.1')
    else
        writeln('incorrect');

    if 2.1 < 1.1 then
        writeln('incorrect')
    else
        writeln('2.1 is not less than 1.1');

    if 1.1 <= 2.1 then
        writeln('1.1 is leq 2.1')
    else
        writeln('incorrect');

    if 2.1 <= 2.1 then
        writeln('2.1 is leq 2.1')
    else
        writeln('incorrect');

    if 1.1 <> 2.1 then
        writeln('1.1 is neq 2.1')
    else
        writeln('incorrect');

    if 2.1 <> 2.1 then
        writeln('incorrect')
    else
        writeln('2.1 is not neq 2.1');

    if 1.1 = 2.1 then
        writeln('incorrect')
    else
        writeln('1.1 is not eq 2.1');

    if 1.1 > 2.1 then
        writeln('incorrect')
    else
        writeln('1.1 is not greater than 2.1');

    if 2.1 > 1.1 then
        writeln('2.1 is greater than 1.1')
    else
        writeln('incorrect');

    if 2.1 >= 1.1 then
        writeln('2.1 is geq 1.1')
    else
        writeln('incorrect');

    if 1.1 >= 2.1 then
        writeln('incorrect')
    else
        writeln('1.1 is not geq 2.1');

    if (-0.5) < 3.7 then
        writeln('-0.5 is less than 3.7')
    else
        writeln('incorrect');

    if -0.5 > 3.7 then
        writeln('incorrect')
    else
        writeln('-0.5 is not greater than 3.7');

    if -0.5 < -0.2 then
        writeln('-0.5 is less than -0.2')
    else
        writeln('incorrect');


    onevar := 4.2 * (-3.9);
    othervar := 7.7 / 1.1;

    if myLessThan(onevar,othervar) = 1 then
        writeln('correct! 1');

    if myGreaterThan(onevar, othervar) = 1 then
        writeln('incorrect! 2');

    if myLessThan(othervar,onevar) = 1 then
        writeln('incorrect! 3');

    if myGreaterThan(othervar, onevar) = 1 then
        writeln('correct! 4');

    if myLessThan(1.1, 2.1) = 1 then
        writeln('correct! 5');

    if myLessThan(2.1, 1.1) = 1 then
        writeln('incorrect! 6');

    if 1.1 < 2.1 then
        writeln('correct! 7');

    if myGreaterThan(1.1, 2.1) = 1 then
        writeln('incorrect! 8');

    if myGreaterThan(2.1, 1.1) = 1 then
        writeln('correct! 9');

    if 2.1 > 1.1 then
        writeln('correct! 10');

    
end.
