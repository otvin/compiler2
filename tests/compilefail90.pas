program compilefail90(output);
{known bug from January 11, 2020; fixed January 25, 2020}
{renamed from testbugfix02 on November 16, 2025}

type myrange = -10..10;
var q:myrange;
begin
    q := -11;  {should be caught at compile-time, was then only caught at run-time}
end.
