program testfunctions08(output);
{tests real params and returns in functions}


function realfunc2(r:Real):Real;
begin
    realfunc2 := r * 2.0;
end;

begin
    writeln(realfunc2(13.0));
end.
