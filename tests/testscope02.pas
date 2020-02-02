program testscope02(output);
{tests combination of byref and global var scope}

var globalint:integer; globalreal:real; tmp:integer;

function byRef(var a:integer; var b:real):integer;
begin
  writeln('Before ');
  writeln(a);
  writeln(globalint);

  a := a + 2;
  globalint := globalint + 2;

  writeln('After ');
  writeln(a);
  writeln(globalint);

  writeln('Before Real');
  writeln(b);
  writeln(globalreal);

  b := b * 2;
  globalreal := globalreal * 2;

  writeln('After Real');
  writeln(b);
  writeln(globalreal);

  byRef := 0;
end;

function byVal(a:integer; b:real):integer;
begin
  writeln('Before ');
  writeln(a);
  writeln(globalint);

  a := a + 2;
  globalint := globalint + 2;

  writeln('After ');
  writeln(a);
  writeln(globalint);

  writeln('Before Real');
  writeln(b);
  writeln(globalreal);

  b := b * 2;
  globalreal := globalreal * 2;

  writeln('After Real');
  writeln(b);
  writeln(globalreal);

  byVal := 0;
end;

begin {main}
  globalint := 9;
  globalreal := 3.7;

  writeln('in main going in');
  writeln(globalint);
  writeln(globalreal);
  tmp := byval(globalint, globalreal);
  writeln('in main coming out');
  writeln(globalint);
  writeln(globalreal);

  writeln('in main going in2');
  writeln(globalint);
  writeln(globalreal);
  tmp := byref(globalint, globalreal);
  writeln('in main coming out2');
  writeln(globalint);
  writeln(globalreal);

  writeln('in main going in3');
  writeln(globalint);
  writeln(globalreal);
  tmp := byval(globalint, globalreal);
  writeln('in main coming out3');
  writeln(globalint);
  writeln(globalreal);
end.
