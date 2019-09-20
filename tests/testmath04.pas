program testmath04(output);
{test modulo function}
var a:Integer;
begin
  a := 10 mod 3;
  writeln(a);
  a := -147 mod 19;
  writeln(a);
  a := 58 mod 7;
  writeln(a);
  a := -1973 mod 29;
  writeln(a);
  a := (4 * 7) mod (-3 * (-7));
  writeln(a);
end.
