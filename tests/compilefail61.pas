program compilefail61(output);
{string literal of incorrect size, being assigned to a string-type}
type
	Length = 1..10;
	mystring = packed array[Length] of char;

var alpha:mystring;


begin
	alpha := 'hello!';  {needed to be padded with spaces to a length of 10}
	writeln(alpha);
end.
