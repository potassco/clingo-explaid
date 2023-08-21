% Transformed Program

{selected(a)}.
{selected(b)}.
{selected(c)}.
{selected(d)}.

a :- selected(a).
b :- selected(b).
c :- selected(c).
d :- selected(d).


{x;y}.

:- b, c.
:- a.
:- c, d.

#show selected/1.
