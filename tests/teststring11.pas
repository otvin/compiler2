program teststring11(output);
{byref strings}

type mystring = packed array[1..15] of char;

var a:mystring;

procedure capitalize(var s:mystring);
var c:char;
begin

	c := s[1];

	if (c >= 'a') and (c <= 'z') then
		s[1] := chr(ord(c) - 32);

end;


begin

	a := 'giraffe        ';
	capitalize(a);
	writeln(a,'*');
end.

