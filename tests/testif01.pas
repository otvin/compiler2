program testif01;

begin
    if 3 < 5 then
        writeln('three is less than five');

    if 7 > 2 then
        begin
            writeln('seven is greater than two');
            writeln('that is what I said!');
        end;

    if 42 >= 44 then
        writeln('oopsie this should not show')
    else
        writeln('forty-two is not greater than or equal to 44');
    
end.
