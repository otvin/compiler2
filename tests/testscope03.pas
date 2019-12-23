program testscope03(output);
var i:integer; j:real;
function f(i:integer):integer;
var j:real;
begin
  j:=i * 1.2;
  f:=i-1;
end;
function q(j:real):real;
var i:integer;
begin
  i:=7;
  q:=j*i;
end;
begin {main}
  i:=3;
  j:=1.1;
  i:=f(i);
  j:=q(j);
  writeln(i,':',j);
end.
