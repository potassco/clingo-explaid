num(1..4).
{a(1..4)}.

b(X) :- num(X), not a(X).

c(X+Y) :- a(X), b(Y).

:- a(X), a(X+1).
:- not b(4).
