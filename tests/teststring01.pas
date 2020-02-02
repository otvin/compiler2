program teststring01(output);
type String = packed array[1..12] of char;
var hw:String;
begin
  hw:='Hello World!';
  writeln(hw);
end.
