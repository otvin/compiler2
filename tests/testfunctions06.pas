program testfunctions06(output);
var i:integer;

function q(x:integer;y:integer):integer;
begin
    q:=x*y
end;

function r(z:integer):integer;
begin
    r:=q(z+2,z-2)
end;

function works(one:integer;two:integer):integer;
begin
    works:=q(one,two)
end;

begin
    i := 10;
    writeln(q(i+2,i-2));
    writeln(works(i+2,i-2));
    writeln(r(i))


end.
