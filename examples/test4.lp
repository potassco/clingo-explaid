{a}. {b}. {c}.

% {a; b}.

unsat :- a, b.
unsat :- not a, not b.

:- not unsat.
:- not a, not b, not c.

#heuristic a.[1,false]
#heuristic b.[1,false]
#heuristic c.[1,false]
