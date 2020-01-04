program testboolean02(output);

var i, i1, j, j1:Boolean;

begin
	i := True;
	j := False;

	if i <= j then 
		writeln('bad! i <= j');

	if j <= i then
		writeln('false correctly implies true');

	if i <= True then
		writeln('true correctly implies true');

	if False <= j then
		writeln('false correctly implies false');

	if i <> j then
		writeln('true does not equal false');

	if i = True then
		writeln('true equals true');

	if j = False then
		writeln('false equals false');

	i1 := not j;

	j1 := not i;

	writeln('couple more ways to write True: ', not j, ' ', i1);
	writeln('couple more ways to write False: ', not i, ' ' , j1);

	if i and (not j) then
		writeln('True and (not False) is true!');

	writeln('');
	writeln('truth tables');
	writeln('True and True = ', i and i1);
	writeln('True and False = ', i and j);
	writeln('False and True = ', False and i1);
	writeln('False and False = ', j and j1);
	writeln('');
	writeln('True or True = ', i or i1);
	writeln('True or False = ', i or j);
	writeln('False or True = ', j or i1);
	writeln('False or False = ', False or j1);
	writeln('');
	writeln('XOR is done with the <> operator');
	writeln('True xor True = ', i <> i1);
	writeln('True xor False = ', True <> j);
	writeln('False xor True = ', j1 <> i);
	writeln('False xor False = ', j <> j1);
	writeln('');
	writeln('False = True ', i = j);
	writeln('True = False ', j1 = i1);

end.
