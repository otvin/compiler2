program testfunctions07(output);
{testing composed functions}


var i:integer;

function f(a:integer):integer;
begin
    f := a + 7
end;

function g(b:integer):integer;
begin
    g := b * 2
end;

function h(c:integer):integer;
begin
    h := c - 11
end;



begin
    writeln(f(g(h(4))));  {should be -7}
    writeln(g(h(f(17))))  {should be 26}

end.
