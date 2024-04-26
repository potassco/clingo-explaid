#program base.
{ a; b; c; d }.
x(1).
#true :- x(2).
unsat :- a; b; c.
unsat :- a; d.
