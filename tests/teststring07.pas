program teststring07(output);
type
	Length = 1..10;
	mystring = packed array[Length] of char;

var alpha:mystring;


begin
	alpha := 'hello!    ';
	writeln(alpha);
end.
