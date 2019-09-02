program testglobalvar01;
var
    fred : integer;
    joe : integer;

begin
    fred := -4;
    joe := fred * 2;
    joe := joe + fred;  { this is a multi-line comment
        and should be ignored }

    writeln('This should be negative 12: ');
    writeln(joe)
end.
