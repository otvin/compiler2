program testbyref01(output);

function myfunc(a:integer; var b:integer):Integer;
begin
    b := b + a;
    myfunc := a + b;
end;

function firstfunc(q:integer):Integer;
var r:integer; s:integer;
begin
    r := q * 2;
    write('before calling myfunc, r = ');
    writeln(r);
    s := myfunc(q, r);
    write('after calling myfunc, r = ');
    writeln(r);
    firstfunc := s;
end;

begin
    writeln(firstfunc(17));
end.
