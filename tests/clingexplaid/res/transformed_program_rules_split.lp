#program base.
constant.
_body("Ym9keSgxKQ==",(1,)) :- body(1).
_body("Ym9keSgyLFgsWSk=",(X,Y,2)) :- body(2,X,Y).
_body("Ym9keShYKQ==",(X,)) :- body(X).
_body("Y29uc3RyYWludA==",()) :- constraint.
head(1) :- _body("Ym9keSgxKQ==",(1,)).
head(2) :- _body("Ym9keSgyLFgsWSk=",(X,Y,2)).
head(3) :- _body("Ym9keShYKQ==",(X,)).
#false :- _body("Y29uc3RyYWludA==",()).
