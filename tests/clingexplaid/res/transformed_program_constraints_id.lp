#program base.
{ a; b; c; d }.
x(1).
#true :- x(2).
unsat(1) :- a; b; c.
unsat(2) :- a; d.
