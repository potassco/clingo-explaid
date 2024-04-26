1{a(1..10)}.
a_count(C) :- C=#count{X: a(X)}.
#minimize{C@2: a_count(C)}.
a_sum(S) :- S=#sum{X: a(X)}.
#maximize{S@1: a_sum(S)}.
