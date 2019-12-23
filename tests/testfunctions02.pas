program testfunctions02(output);
var
    a:Integer;
    b:Integer;
    c:Integer;
    d:Integer;

function myfunc(n : Integer) : Integer;
begin
    myfunc := n+1
end;

function otherfunc(q: Integer; r: Integer) :Integer;
begin
    c := q;
    c := c + r;
    otherfunc := c
end;

begin

    a := 9;
    b := myfunc(a);
    writeln('Should be 10');
    writeln(b);

    a := (4 + 2) * 6;
    b := 4;
    d := otherfunc(a,b);
    writeln('Should be 40');
    writeln(d);

    a := 77 DIV 11;
    b := myfunc(a);
    writeln('Should be 8');
    writeln(b)

end.
