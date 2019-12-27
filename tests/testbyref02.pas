program testbyref02(output);


function myfunc2(var b:real):real;
begin
    b := b * 0.5;
    myfunc2 := b * 1.7;
end;

function firstfunc(q:Real):Real;
var r:real; s:real;
begin
    r := q - 1;
    write('before calling myfunc, r = ');
    writeln(r);
    s := myfunc2(r);
    write('after calling myfunc, r = ');
    writeln(r);
    firstfunc := s;
end;

begin
    writeln(firstfunc(39.0));
end.
