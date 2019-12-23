program testmath03(output);
{Among other things, this tests idiv with a negative number}


function f(x:integer):integer;
begin
    f:=x+4
end;
function g(x:integer): integer;
begin
    g:=x DIV 2
end;
function h(x:integer): integer;
var a:integer;
begin
    a:=x*8;
    h:=a
end;
function i(x:integer): integer;
var a:integer;
begin
    a:=x-10;
    i:=a
end;
function j(x:integer): integer;
var a:integer; b:integer;
begin
    a:=3;
    b:=i(x);
    j:=x+a
end;




begin
    writeln('should be 20');
    writeln(f(g(h(i(14)))));

    
    writeln('should be -32');
    writeln(f(g(h(i(j(-2))))))

end.
