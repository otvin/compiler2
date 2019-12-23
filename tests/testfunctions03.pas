program testfunctions03(output);

function maxoftwo(one : Integer; two: Integer) : Integer;
begin
    if one > two then
        maxoftwo := one
    else
        maxoftwo := two
end;

function maxofthree(one : Integer; two: Integer; three: Integer) : Integer;
begin
    if one > two then
        if one > three then
            maxofthree := one
        else
            maxofthree := three
    else
        if two > three then
            maxofthree := two
        else
            maxofthree := three
end;


begin

    writeln('max of 3 and 4 is:');
    writeln(maxoftwo(3,4));

    writeln('max of (8*6) and (7*7) is:');
    writeln(maxoftwo((8*6), (7*7)));

    writeln('max of 1, -4, and -2 * -2 is');
    writeln(maxofthree(1, -4, -2 * (-2)))

end.
