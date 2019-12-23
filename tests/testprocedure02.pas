program testprocedure02(output);
{was "testproc01" in the old compiler test suite}

procedure f(i:integer);
var q:integer;
begin
     q := 0;
     if i > 0 then
        begin
             while q < i do
             begin
                   write('*');
                   q := q + 1;
             end;
        writeln('');
        end
end;

function l(r:integer):integer;
begin
     l:=r+1;
end;

begin {main}
      f(7);
      f(2);
      f(4);
      f(l(5));
end.
