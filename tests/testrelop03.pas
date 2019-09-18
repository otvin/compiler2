program testrelop03(output);
var
	b:Boolean;
begin
	b:=7 < 5;
	writeln(1,'. Should be false: ',b);

	b:= 6.2 <= (9 * 8 + 7);
	writeln(2, '. Should be true: ', b);

	b:= (-37 * 1) = -37;
	writeln(3,'. Should be true: ', b);

	b:= false <= true;
	writeln(4,'. Should be true: ', b);

	b:= 72 <> (72 - 0);
	writeln(5,'. Should be false: ', b);

	b:= 123098 >= 1230;
	writeln(6, '. Should be true: ', b);

	b:= 9812.398 > -320.772;
	writeln(7, '. Should be true: ', b);
end.
