program testreal08(output);{comment}

{test bugfix of a comment right after the program statement, also tests passing int values 
 for real parameters}


var myint:integer;
function absolutevalue(i:real):real;
begin
  if i < 0.0 then
    absolutevalue := -1.0 * i
  else
    absolutevalue := i
end;

begin {main}
  myint := -4;
  writeln(absolutevalue(1));
  writeln(absolutevalue(myint));
end.
