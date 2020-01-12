program compilefail48(output);
{try to pass control variable of for statement into a procedure byref}

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

procedure writethenextnato(var pp:nato);
begin

	pp := succ(pp);

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

	for myalpha := alpha to echo do
		begin
			writethenato(myalpha);
			writethenextnato(myalpha);
		end;
	
end.
	
