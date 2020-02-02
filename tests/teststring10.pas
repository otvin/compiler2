program teststring10(output);
{passing strings and literals in as string parameters}

type
	Length = 1..10;
	mystring = packed array[Length] of char;

var alpha,beta,charlie,delta:mystring;

procedure printit(a:mystring);
begin
	write(a);
	writeln('*');
end;


begin
	alpha := 'atlanta   ';
	beta := 'bueno     ';
	charlie := 'chatter   ';
	delta := 'dingdong  ';

	printit(alpha);
	printit(beta);
	printit('what?     ');
end.
