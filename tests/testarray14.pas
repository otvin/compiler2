program testarray14(output);
{iso required functions on an array with component type char}


var

	arr1: array[1..7] of char;

begin

	arr1[1] := 'l';
	arr1[2] := succ(arr1[1]);

	writeln(arr1[2]);

	if arr1[2] = 'm' then
		writeln('test 1 passed');


end.
