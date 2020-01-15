program testtypedef11(output);
{test creation of anonymous types}

var
	YearsToGettysburg: 0..86;
	fruits,groceries:(apple,cherry,banana);


begin

	fruits := apple;
	groceries := succ(fruits);
	if groceries = cherry then 
		writeln('yes!');

	YearsToGettysburg := 47;
	YearsToGettysburg := YearsToGettysburg + 19;
	writeln(YearsToGettysburg);

	writeln('And now an error for exceeding subrange...');
	YearsToGettysburg := YearsToGettysburg * 2;
	writeln(YearsToGettysburg);

end.
	
