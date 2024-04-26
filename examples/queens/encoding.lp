#const n=5.
number(1..n).
cell(X,Y) :- number(X), number(Y).

1 { queen(X,Y): number(Y) } 1 :- number(X).
1 { queen(X,Y): number(X) } 1 :- number(Y).

:- 2 { queen(D-J,J) }, D = 2..2*n.
:- 2 { queen(D+J,J) }, D = 1-n..n-1.
