program testtypedef03(output);

type fruit = (apple, pear, banana, cherry);

var myfruit:fruit;

begin
	myfruit := apple;
	writeln('it''s apple');
	myfruit := succ(myfruit);
	writeln('now it''s pear');
	myfruit := succ(myfruit);
	writeln('now it''s banana');
	myfruit := succ(myfruit);
	writeln('now it''s cherry');
	writeln('next line should fail with an error');
	myfruit := succ(myfruit);
	writeln('we shouldn''t get here.');

end.
