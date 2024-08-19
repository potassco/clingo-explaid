{a(1..3)}.
{b(1..3)}.

a(X) :- b(X+1), X>0.
:- a(X), b(X).

#maximize{X: b(X)}.
