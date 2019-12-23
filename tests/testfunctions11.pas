program testfunctions11(output);
{tests that you can pass an integer literal into a real parameter in a function}


function simpleFunc(a:Real):Real;
begin
    simpleFunc := a;
end;


begin
    writeln(simpleFunc(3));
end.
