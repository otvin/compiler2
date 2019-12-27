program testbyref03(output);
{among other things, tests taking a byref param, and passing it into a second function as byval}

var myglobal:integer; myglobalreal:real;

function byValEditInt(a:Integer):Integer;
begin
    a := a + 1;
    byValEditInt := a div 2;
end;

function byRefCallByValInt(var a:Integer):Integer;
begin
    write ('a is this ');
    writeln(a);
    a := a + 1;
    write ('a is now this ');
    writeln(a);
    byRefCallByValInt := byValEditInt(a);
    write ('a is now this ');
    writeln(a);
end;

function testByRefInt(a:Integer):Integer;
var b:Integer;
begin
    b := a * 2;
    write('Before a byval edit call, b = ');
    writeln(b);
    write('func returns: ');
    writeln(byValEditInt(b));
    write('After byval edit call, b = ');
    writeln(b);
    writeln('');
    writeln('reset b');
    b := a - 9;
    write('Before byref edit call, b = ');
    writeln(b);
    writeln('func returns: ');
    writeln(byRefCallByValInt(b));
    write('After byref edit call, b = ');
    writeln(b);
    writeln('');
    testByRefInt := -2
end;


begin

    myglobal := testByRefInt(42);
    write ('master func = ');
    writeln(myglobal);

    myglobal := testByRefInt(-37);
    write ('master func = ');
    writeln(myglobal);
end.
