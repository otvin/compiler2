program testrelop01(output);
var
    small : integer;
    medium : integer;
    large: integer;
    huge: integer;
    numSuccess : integer;

begin
    small := -98765;
    medium := (8 * (2 + 7)) DIV 4;
    large := 2 * 4 * 6 * 8;
    huge := 100000 + (7 * (4 + 2));
    numSuccess := 0;

    if small < large then
        begin
            writeln ('Less than success');
            numSuccess := numSuccess + 1
        end;

    if small <= large then
        begin
            writeln ('Less than equal success 1');
            numSuccess := numSuccess + 1
        end;

    if medium <= medium then
        begin
            writeln ('Equal things are less than or equal to');
            numSuccess := numSuccess + 1
        end;

    if huge < small then
        writeln ('SHOULD NOT SEE THIS: Huge is not less than small.');

    if medium = large then
        writeln ('SHOULD NOT SEE THIS: Medium is not equal to large.');

    if medium <> large then
        begin
            writeln ('Not Equal Success');
            numSuccess := numSuccess + 1
        end;

    if huge <> huge then
        writeln ('Should not see this! huge is not not equal to itself.');

    if large > (3 * 5 * 7 * 9) then
        begin
            writeln ('Should not see this!  Large is not bigger than this number.')
        end;

    if 3 * 5 * 7 * 11 > large then
        begin
            writeln ('Success - a larger number is larger than large.');
            numSuccess := numSuccess + 1
        end;

    if 200000 >= small then
        begin
            writeln ('Another success');
            numSuccess := numSuccess + 1
        end;

    if small >= small then
        begin
            writeln ('Small is greater than or equal to itself.');
            numSuccess := numSuccess + 1
        end;

    writeln('If all is good, number of successes below will be 7.');
    writeln(numSuccess)

end.
