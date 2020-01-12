program undefinedbehavior01(output);
{Uses functions involving the control variable to try to set the initial and final values of a for statement.
 The actual output here is typically 0, because a is typically set to 0 even though it's uninitialized and 
 should not be used.  It is a runtime error to use a variable before it is initialized, but we do not do that yet.

 FreePascal gives a warning that a is undefined before it is used, but otherwise generates the same output}


var a,b,Counter:integer;

function threetimes(a:integer):integer;
begin
	threetimes := 3 * a;
end;

function sixtimes(a:integer):integer;
begin
	sixtimes := 6 * a;
end;

begin
	b := 7;

	for a := threetimes(a) to sixtimes(a) do 
		begin
			writeln(a);
		end;	

end.
