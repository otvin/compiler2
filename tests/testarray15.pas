program testarray15(output);
{testing arrays where the index expression involves another array reference}


var

	arr1: array[1..7] of char;
	arr2: array[1..5] of integer;

begin

	arr2[3] := 4;

	arr1[arr2[3]] := 'a';

	writeln(arr1[4]);


end.
