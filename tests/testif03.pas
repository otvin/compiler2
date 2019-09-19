program testif03;
var
    numSuccess:Integer;
    a:Integer;


begin

    numSuccess := 0;
    a := 4;

    if a = 4 then
        begin
            numSuccess := numSuccess + 1;
            writeln('yes, a equals 4')
        end
    else
        begin
            writeln('oops - else should not have fired')
        end;

    if a > 5 then
        writeln('oops - 4 is not greater than 5')
    else
        begin
            numSuccess := numSuccess + 1;
            writeln('else statement worked - 4 is not greater than 5')
        end;

    writeln('If all is good, number of successes below will be 2.');
    writeln(numSuccess)

end.
