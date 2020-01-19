program testarray04(output);

type
	subr = 1..10;
	myarr = array[subr] of integer;

var
	arr:myarr;
	i,j:integer;

begin

	for i := 1 to 10 do 
		begin
			arr[i] := i;
		end;

	j := 0;

	for i := 1 to 10 do
		begin
			j := j + arr[i];
		end;

	writeln('should be 55: ', j);

end.

