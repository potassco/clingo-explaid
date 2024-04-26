#program base.
a(1) :- _rule(1).
b(2) :- x; _rule(2).
c(3); c(4) :- x; _rule(3).
d((10..15)) :- _rule(4).
e(16) :- _rule(5).
f(17); f(18) :- e(16); _rule(6).
x(19) :- _rule(7).
{_rule(1..7)} % Choice rule to allow all _rule atoms to become assumptions
