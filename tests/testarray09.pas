program testarray09(output);
{test array bounds check failure on the high side of the subrange with enumerated types}

type
	color = (red, orange, yellow, green, blue, indigo, violet);
	subc = orange..indigo;
	colorarray = array[subc, subc] of boolean;	

var
	c,d:color; arr:colorarray;

begin

	for c := orange to indigo do begin
		for d:= indigo downto orange do begin
			if c = d then 
				arr[c,d] := True
			else
				arr[c,d] := False;
		end;
	end;

	writeln('You should see 5 rows of various false and true and then an error.');
	for c := orange to violet do begin
		for d := orange to indigo do begin
			write(arr[c,d], ' ');
		end;
		writeln;
	end;

end.
