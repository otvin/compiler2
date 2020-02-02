program teststring08(output);
{test relational operators with strings}
type
	Length = 1..10;
	mystring = packed array[Length] of char;

var alpha,beta,charlie,delta:mystring;


begin
	alpha := 'apple     ';
	beta := 'banana    ';
	charlie := 'grapevine ';
	delta := 'bananas   ';

	if alpha < beta then
		writeln('correct 1');

	if delta <= beta then
		writeln('oops')
	else
		writeln('correct 2');

	if charlie = delta then
		writeln('oops')
	else
		writeln('correct 3');

	if delta <> beta then
		writeln('correct 4');

	if alpha > charlie then
		writeln('oops')
	else
		writeln('correct 5');

	if charlie >= charlie then
		writeln('correct 6');

	if charlie >= beta then
		writeln('correct 7');

end.
