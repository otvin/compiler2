program testfunctions09(output);


function realfunc2(r:Real):Real;
begin
    r := r + 7;
    realfunc2 := r * 2.0;
end;

begin
    writeln(realfunc2(13.0));
end.
