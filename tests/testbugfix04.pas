program testbugfix04(output);
{Bug discovered Nov 8 2025.

Previous parsing of <simple-expression> ::= [sign] <term> only looked for minus signs.
Added support for parsing plus signs.
}

var a:integer;
begin
    a := +10;  
    writeln(a); {should display 10}
    a := (+10);
    writeln(a); {should also display 10}
end.
