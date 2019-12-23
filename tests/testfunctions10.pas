program testfunctions10(output);
{tests real division, but also tests passing maximum number of parameters to a function}


function realdiv(n:Real;d:Real):Real;
begin
    realdiv := n/d;
end;

function realfuncy(a:Real;b:Real;c:Real;d:Real;e:Real;a1:Integer; a2:Integer; f:Real
    ;a3:Integer; g:Real; h:Real; a4:Integer; a5:Integer; a6:Integer):Real;
var
    localR:Real;
    localI:Integer;
begin
    localI := a1 + a2 + a3 + a4+ a5+ a6;
    localR := a + b + c + d + e + f + g + h;

    realfuncy := localI + localR;

end;

begin
    writeln(realdiv(88.0,3.7));
    writeln(realfuncy(1.1,2.2,3.3,4.4,5.5,1,2,6.6,3,7.7,8.8,4,5,6));
end.
