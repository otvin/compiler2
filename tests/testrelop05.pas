program testrelop05(output);
{relational operators with enumerated types}

type fruit = (apple, pear, banana, cherry, guava, mango);

var myfruit, myotherfruit:fruit;

begin
	myfruit := cherry;
	myotherfruit := pear;

	if myotherfruit < myfruit then
		writeln('pear is less than cherry');

	myfruit := pred(myfruit);

	if myfruit > myotherfruit then
		writeln('banana is greater than pear');

	myfruit := pred(myfruit);

	if myfruit > myotherfruit then
		writeln('oops!')
	else
		writeln('pear is not greater than pear');

	if myfruit = myotherfruit then 
		writeln('pear is equal to pear');

	myotherfruit := succ(succ(succ(myotherfruit)));

	if myotherfruit <> myfruit then
		writeln('guava and pear are not equal');

end.
