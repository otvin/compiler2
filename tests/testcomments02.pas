program testcomments02(output);

begin
    (* test alternate comment string *)

    { test Note 1 from 6.1.8 }
    { test open with brace close with alternate *)
    (* test open with alternate close with brace }

    { test Note 2 from 6.1.8 }
    { a commentary may contain this sequence: {) }
    writeln(0);
end.
