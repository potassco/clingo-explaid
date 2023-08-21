% Transformed Program

{selected(a)}.
{selected(b)}.
{selected(c)}.
{selected(d)}.

a :- selected(a).
b :- selected(b).
c :- selected(c).
d :- selected(d).

% {a;b;c}.

% selected(a) :- a.
% selected(b) :- b.
% selected(c) :- c.

% #heuristic selected(_). [1,false]
% #heuristic a. [1,false]
% #heuristic b. [1,false]
% #heuristic c. [1,false]

% t.

{x;y}.

% d(1); d(2) :- t.
:- b, c.
:- a.
:- c, d.

#show selected/1.
