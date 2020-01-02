program testconst02(output);
{tests constants in procedures, including constants with different values in different scopes}
const 
	maxthis = 80;
	minthis = -4.28;
	somestring = 'my string';

procedure testconsts(a:integer; b:real);
const
	localone = 1;
	minthis = -5.96;  {redefined name}
begin
	writeln ('here, minthis should be -5.96: ', minthis);	
	writeln (a + maxthis + localone);  {references a local and global constant}
	writeln(b * (11.92 / minthis));
end;


begin
	
	writeln('here, minthis should be -4.28: ', minthis);
	writeln('next two results should be 88 and 4.0');
	testconsts(7, 2.0);
	
end.
