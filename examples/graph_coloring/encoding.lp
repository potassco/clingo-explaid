{assign(N, C): color(C)}=1 :- node(N).

:- edge(N1, N2), assign(N1, C), assign(N2, C).

#show assign/2.
