program testtypedef05(output);
{test passing user-defined enumerated types byval and byref to procedures and returning enumerated type from function}

type nato = (alpha, bravo, charlie, delta, echo, foxtrot, golf, hotel, india, juliett, kilo, lima, mike);

var a,b:nato;

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


function doublepred(n:nato):nato;
var c:nato;
begin
	if n > alpha then
		c := pred(n)
	else
		c := n;


	if c > alpha then 
		c := pred(c);

	doublepred := c;
end;


procedure succtotwovariables(var y,z:nato);
begin
	if y < mike then 
		y := succ(y);

	if z < mike then
		z := succ(z);
end;


procedure foo(u,v:nato);
var d:nato;
begin
	write('v = ');
	writethenato(v);
	d := doublepred(v);
	write('doublepred on that d = ');
	writethenato(d);
	write('and u = ');
	writethenato(u);
	succtotwovariables(d,u);
	write('now d = ');
	writethenato(d);
	write('and now u = ');
	writethenato(u);
end;

begin
	a := echo;
	b := foxtrot;

	write('before, a and b equal ');
	writethenato(a);
	writethenato(b);
	foo(a,b);
	write('after, a and b equal ');
	writethenato(a);
	writethenato(b);

	writeln('now let''s do it again ');

	a := india;
	b := delta;

	write('before, a and b equal ');
	writethenato(a);
	writethenato(b);
	foo(a,b);
	write('after, a and b equal ');
	writethenato(a);
	writethenato(b);
end.

	
	
