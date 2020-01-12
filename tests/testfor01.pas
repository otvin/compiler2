program testfor01(output);

type nato = (alpha, bravo, charlie, delta, echo, foxtrot, golf, hotel, india, juliett, kilo, lima, mike);
	slim = delta..hotel;

var i:integer; myalpha:nato; c:char; s:slim;

procedure writethenato(pp:nato);
begin
	if pp = alpha then writeln('alpha');
	if pp = bravo then writeln('bravo');
	if pp = charlie then writeln('charlie');
	if pp = delta then writeln('delta');
	if pp = echo then writeln('echo');
	if pp = foxtrot then writeln('foxtrot');
	if pp = golf then writeln('golf');
	if pp = hotel then writeln('hotel');
	if pp = india then writeln('india');
	if pp = juliett then writeln('juliett');
	if pp = kilo then writeln('kilo');
	if pp = lima then writeln('lima');
	if pp = mike then writeln('mike');
end;

begin

	for i := 1 to 3 do
		begin
			writeln(i);
		end;

	writeln('try again');

	for i := 17 downto -4 do
		begin
			writeln(i);
		end;

	writeln ('now for nato');

	for myalpha := delta to kilo do
		begin
			writethenato(myalpha);
		end;

	writeln ('next loop shouldn''t print anything');

	for myalpha := charlie downto juliett do
		begin
			writethenato(myalpha);
		end;

	writeln ('now back to writing');

	for myalpha := foxtrot downto charlie do
		begin
			writethenato(myalpha);
		end;

	writeln ('now characters');

	for c := 'k' to 'z' do
		begin
			writeln(c);
		end;

	for c := 'Q' downto 'L' do
		begin
			writeln(c);
		end;

	writeln ('and subranges');
	for s := echo to golf do
		begin
			writethenato(s);
		end;

	writeln ('and now an error');

	for s := foxtrot downto bravo do
		begin
			writethenato(s);
		end;

end.
