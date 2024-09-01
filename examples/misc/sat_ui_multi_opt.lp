{a(1..3)}.
{b(1..3)}.
c(1).

a(X) :- b(X+1), X>0.
:- a(X), b(X).

#maximize{X@1: c(X)}.
#minimize{X@2: c(X)}.
