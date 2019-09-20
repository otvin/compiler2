program testglobalvar02(output);
var
    fred, joe : integer;

begin
    fred := -4;
    joe := -2 * 3;


    if joe = fred then
        writeln('SHOULD NOT SEE THIS!!! JOE DOES NOT EQUAL FRED!!!');

    if fred = -4 then
        writeln('fred equals -4');

    if fred = -2 * (1 + 1) then
        writeln('fred equals -2 * (1 + 1)')


end.
