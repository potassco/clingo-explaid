{a}. {b}. {c}.

% {a; b}.

unsat :- a, b.
unsat :- not a, not b.

:- not unsat.
