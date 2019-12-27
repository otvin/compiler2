program testbyref04(output);

function functhree(var a:Integer; var b:real):integer;
begin
  write('A = ');
  writeln(a);
  a := a + 2;
  write('A = ');
  writeln(a);

  functhree := 1;
end;

function functwo(var a:Integer; b:real):integer;
begin
  write('a = ');
  writeln(a);
  a := a + 1;
  write('a = ');
  writeln(a);

  functwo := functhree(a, b);
  write('a = ');
  writeln(a);
end;

function funcone(a:integer):integer;
var q:integer; s:integer;
begin
  q := 7;

  writeln(q);
  s := functwo(q,6.7);
  writeln(q);
  funcone:=0;
end;

begin {main}
  writeln(funcone(1));
end.
