%#const min_assumptions=10.
%#const max_assumptions=100.
%#const min_mus=1.
%#const max_mus=10.
%#const min_mus_assumptions=1.
%#const max_mus_assumptions=100.

1{assumptions(min_assumptions..max_assumptions)}1.
a(1..N) :- assumptions(N).

1{mus(min_mus..max_mus)}1.
m(1..N) :- mus(N).

% --- [ GENERATING MUS ] -----------------------------------------------------------------------------------------------

min_mus_assumptions{contains(M,A) : a(A)}max_mus_assumptions :- m(M).

% --- [ VALIDATING MUS ] -----------------------------------------------------------------------------------------------

subset(M1,M2) :- m(M1), m(M2), M1!=M2,
                 SIZE_M1=#sum{1,A: contains(M1,A)}, OVERLAP=#sum{1,A: contains(M1,A), contains(M2,A)},
                 SIZE_M1=OVERLAP.
:- subset(M1,M2).
