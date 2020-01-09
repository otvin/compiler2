program testtypedef04(output);

type fruit = (apple, pear, banana, cherry);

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
