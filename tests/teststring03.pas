program teststring03(output);
type String = packed array[1..12] of char;
var hw:String;
  hw2:String;
begin
  hw:='Hello World!';
  hw2:=hw;
  writeln(hw2);
end.
