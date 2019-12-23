program testfunctions04(output);

{test functions that call other functions}

function plustwo(q : Integer) : Integer;
begin
    plustwo := q +2
end;

function funcB(b : Integer) : Integer;
begin
    funcB := (b+2) * (b-4)
end;

function funcC(r: Integer) : Integer;
begin
    funcC := plustwo(r) * (r-4)
end;

function funcD(s: Integer) : Integer;
var
    tmp : Integer;
begin
    tmp := plusTwo(s);
    funcD := tmp * (s-4)
end;

begin {main program}

    writeln(funcB(8));
    writeln(plustwo(2));
    writeln(funcC(12));
    writeln(funcD(-7))

end.
