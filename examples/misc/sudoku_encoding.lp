% ########### SUDOKU SOLVER ###########

% GENERATING

% #const subgrid_size=2/3.

number(1..2**2).

solution(X,Y,V) :- initial(X,Y,V).
{solution(X,Y,N): number(N)}=1 :- number(X) ,number(Y).
cage(X1,Y1,X2,Y2):- solution(X1,Y1,_), solution(X2,Y2,_), ((X1-1)/subgrid_size)==((X2-1)/subgrid_size), ((Y1-1)/subgrid_size)==((Y2-1)/subgrid_size).

:- solution(X,Y1,N), solution(X,Y2,N), Y1 != Y2.
:- solution(X1,Y,N), solution(X2,Y,N), X1 != X2.
:- cage(X1,Y1,X2,Y2), solution(X1,Y1,N), solution(X2,Y2,N), X1!=X2, Y1!=Y2.

#show solution/3.
