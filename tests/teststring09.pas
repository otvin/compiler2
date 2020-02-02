program teststring09(output);
{test relational operators with string literals}

type
	Length = 1..10;
	mystring = packed array[Length] of char;

var alpha,beta,charlie,delta:mystring;


begin
	alpha := 'atlanta   ';
	beta := 'bueno     ';
	charlie := 'chatter   ';
	delta := 'dingdong  ';

	if 'apple' < 'pear ' then
		writeln('correct 1');

	if 'BUENO     ' <= beta then
		writeln('correct 2');

	if 'dingdong  ' = delta then
		writeln ('correct 3');

	if charlie >= 'boo boo   ' then
		writeln ('correct 4');
end.
