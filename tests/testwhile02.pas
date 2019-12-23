program testwhile02(output);
var i:integer;

function fibwhile(seq:integer):integer;
var i:integer; twoago:integer; oneago:integer; current:integer; tmp:integer;
begin
    if seq <= 0 then
        fibwhile := 0
    else if seq = 1 then
        fibwhile := 1
    else

        begin
            twoago:=0;
            oneago:=1;
            current:=1;
            i:=1;

            while i < seq do
                begin
                    current := twoago + oneago;
                    twoago := oneago;
                    oneago := current;
                    i := i + 1
                end;

            fibwhile := current

        end

end;

begin
    i := 1;
    while i < 30 do
        begin
            writeln(fibwhile(i));
            i:=i+1
        end
end.
