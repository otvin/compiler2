program testif02;
var
    fred : integer;
    joe : integer;

begin
    fred := -4;
    joe := -2 * 3;


    if joe = fred then
        writeln('SHOULD NOT SEE THIS!!! JOE DOES NOT EQUAL FRED!!!');

    if fred = -4 then
        begin
            writeln('fred equals -4');
            writeln('and we have a compound statement');
            fred := 1
        end;

    if fred = -2 * (1 + 1) then
        writeln('fred equals -2 * (1 + 1)');

    if fred = 1 then
        writeln('fred equals 1')


end.
