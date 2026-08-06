color(r; g; b).

node(X;Y) :- edge(X,Y).
{ assign(X,C): color(C) } = 1 :- node(X).
:- assign(X,C), assign(Y,C), edge(X,Y).
