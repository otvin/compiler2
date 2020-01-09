program testord03(output);

var myint:integer; b:boolean;

begin
	myint := 437;
	myint := succ(succ(myint));
	writeln ('should be 439: ', myint);

	myint := 1;
	myint := pred(pred(pred(myint)));
	writeln ('should be -2: ', myint);

	b := False;
	writeln('should be True: ', succ(b));

	b := True;
	writeln('should be False: ', pred(b));

	writeln('next line should fail:');
	writeln(succ(b));

end.
