program testarray13(output);
{iso required functions on an array with component type an enumerated type}

type 
	color = (red, orange, yellow, green, blue, indigo, violet);

var

	arr1: array[1..7] of color;

begin

	arr1[1] := yellow;
	arr1[2] := succ(arr1[1]);
	arr1[3] := pred(arr1[1]);
	if arr1[2] = green then
		writeln('test 1 passed');

	if arr1[3] = orange then 
		writeln('test 2 passed');

end.
