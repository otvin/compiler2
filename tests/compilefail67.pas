program compilefail67(output);
{typo in array access}


type q = array[1..5,7..9] of boolean;
var myq:q;


begin
	myq[4[3] := true;
end.
