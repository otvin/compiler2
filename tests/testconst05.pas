program testconst05(output);
{tests character constants vs. string constants.}

const letterq = 'q';

var mychar:char;

procedure writeit(q:char);
begin
	writeln(letterq);
	writeln(q);
end;

begin
	writeln('should be: qqrqq');
	mychar := letterq;
	writeln(mychar);
	writeit('r');
	writeit(letterq);
end.
