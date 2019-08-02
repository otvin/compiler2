program testbugfix01(output);
begin

	{Tests two bugs:

	1) Known Bug reported in README on 2019.07.31

	Floating point literals with a large number of digits will fail to compile, 
	as the compiler currently stores the symbol as a number, and Python loses precision. 
	For example:

    	```writeln(19832792187987.66);```
    
    	results in the following display at program execution:
    
    	```198327921879872.656250000000```

    	however:
    
    	```writeln(1983279218798723.66);```
    
    	results in a compilation error:
    
    	```symboltable.SymbolException: Literal not found: 1983279218798723.8```


	2) Bug discovered during this fix, where the following code would not compile properly:

	```
	writeln(1.23);
	writeln('1.23');
	```

	As the literal table was a single dictionary that stored, as its key, the string value
	of the literal.
	}


	writeln(19832792187987.66);
	writeln(1983279218798723.66);
	writeln(1.23);
	writeln('1.23');

end.
