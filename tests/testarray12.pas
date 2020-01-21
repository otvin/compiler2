program testarray12(output);
{iso required functions on array elements}


var
	arr2: array[3..9] of real;
	arr3: array[-1..4] of char;
	arr4: array[1..10] of integer;

begin


	arr2[3] := 3.14159;
	arr2[4] := sin(arr2[3]);
	arr2[5] := cos(arr2[3]);
	arr2[6] := sqr(arr2[3]);

	writeln(arr2[3], ' ', arr2[4], ' ', arr2[5], ' ', arr2[6]);


	arr3[-1] := chr(65);
	arr3[4] := chr(94);

	writeln(arr3[-1], ' ', arr3[4]);


	arr4[1] := trunc(arr2[3]);
	arr4[2] := ord('a');
	
	writeln(arr4[1], ' ', arr4[2]);


end.
