% Transformed Program

_assumption(a).
_assumption(b).
_assumption(c).
_assumption(d).

{a}. {b}. {c}. {d}.

_muc(a) :- a.
_muc(b) :- b.
_muc(c) :- c.
_muc(d) :- d.

{x;y}.

:- b, c.
:- a.
:- c, d.

