program testbyref06(output);
{ This program was named 'known_bug1' in the original compiler.  The correct output is to print
  8 and then 5, but in the original compiler, it printed 8 and then 0.  In the original, if a real
  valued variable parameter was second in the parameter list, the parameter would get zeroed out.
  Inability to figure out the location in memory for each variable and resolve this bug was one
  of the main things that led me to needing to stop work on compiler and move to compiler2. }


var q:integer; r:real; t:integer;

function functwo(var a:Integer; var b:Real):integer;
begin

  a := a + 1;
  b := b * 1.5;
  writeln(a);
  functwo := a

end;

function funcone(q:Integer):integer;
var one:integer; two:real;

begin
  one := 4;
  two := 3.7;
  funcone := functwo(one,two);
end;

begin {main}
  q:=7;
  r:=9.8;
  t:=functwo(q,r);
  t:=funcone(1);
end.
