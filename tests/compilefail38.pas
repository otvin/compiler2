program compilefail38(output);
{listing same constant multiple times as value of an enumerated type}

type fruit = (apple, pear, banana, cherry, apple);

var myfruit:fruit;

begin
	myfruit := cherry;
	writeln('it''s cherry');
	myfruit := pred(myfruit);
	writeln('now it''s banana');
	myfruit := pred(myfruit);
	writeln('now it''s pear');
	myfruit := pred(myfruit);
	writeln('now it''s apple');
	writeln('next line should fail with an error');
	myfruit := pred(myfruit);
	writeln('we shouldn''t get here.');

end.
