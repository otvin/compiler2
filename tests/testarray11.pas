program testarray11(output);
{arrays based on ordinal types that are not subranges}

type 
	color = (red, orange, yellow, green, blue, indigo, violet);
	chararray = array[char] of integer;
	boolarray = array[boolean] of char;
	colorarray = array[color] of boolean;

var

	arr1, arr1a:chararray;
	arr2:boolarray;
	arr3:colorarray;

begin

	arr1['a'] := 37;
	arr1['b'] := 41;
	arr1a['c'] := arr1['a'] * arr1['b'];
	writeln(arr1['a'], ' ', arr1a['c']);

	arr2[True] := 'a';
	arr2[False] := 'b';

	writeln(arr2[True],arr2[False]);

	arr3[red] := True;
	arr3[blue] := True;
 	if arr3[red] and arr3[blue] then
		writeln('yes!!!');
end.
