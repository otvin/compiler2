program testprocedure07(output);
{test simple byref parameter case}

procedure addone(var i:integer);
begin
	i:=i+1;
end;

procedure b(j:integer);
var z:integer;
begin
	z:=3 + j;
	writeln('before, should be 10: ', z);
	addone(z);
	writeln('after, should be 11: ', z);
end;

begin {main}
	b(7);
end.
