program testarray21(output);
{test multiple arrays as parameters to procedures}

type threebythree = array[1..3,1..3] of integer;

var a,b,c:threebythree;

procedure matrixadd(x,y:threebythree; var z:threebythree);
var i,j:integer;

begin
	i := 1;
	while i <= 3 do begin
		j := 1;
		while j <= 3 do begin
			z[i,j] := x[i,j] + y[i,j];
			j := j + 1;
		end;
		i := i + 1;
	end;
end;

procedure printmatrix(x:threebythree);
var i,j:integer;
begin
	i := 1;
	while i <= 3 do begin
		j := 1;
		while j <= 3 do begin
			write(x[i][j], ' ');
			j := j + 1;
		end;
		writeln;
		i := i + 1;
	end;
end;
	
begin
	a [1,1] := 2;
	a [1,2] := 4;
	a [1,3] := 6;
	a [2,1] := 2;
	a [2,2] := 4;
	a [2,3] := 6;
	a [3,1] := 2;
	a [3,2] := 4;
	a [3,3] := 6;

	b [1,1] := 1;
	b [2,1] := 3;
	b [3,1] := 5;
	b [1,2] := 1;
	b [2,2] := 3;
	b [3,2] := 5;
	b [1,3] := 1;
	b [2,3] := 3;
	b [3,3] := 5;

	matrixadd(a,b,c);

	printmatrix(a);
	writeln;
	printmatrix(b);
	writeln;
	printmatrix(c);
end.
	
