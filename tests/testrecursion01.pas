program testrecursion01(output);

function fib(seq : Integer) : Integer;
begin
    if seq <= 0 then
        fib := 0
    else
        if seq = 1 then
            fib := 1
        else
            fib := fib(seq - 1) + fib(seq - 2)
end;

begin

    writeln(fib(1));
    writeln(fib(2));
    writeln(fib(3));
    writeln(fib(4));
    writeln(fib(5));
    writeln(fib(6));
    writeln(fib(7));
    writeln(fib(8));
    writeln(fib(9));
    writeln(fib(10))


end.
