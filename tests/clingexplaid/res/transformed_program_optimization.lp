#program base.
1 <= { a((1..10)) }.
a_count(C) :- C = #count { X: a(X) }.
a_sum(S) :- S = #sum { X: a(X) }.
