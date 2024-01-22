% ########### SUDOKU SOLVER ###########

% GENERATING

% #const subgrid_size=2/3.

solution(X,Y,V) :- initial(X,Y,V).
{solution(X,Y,N): N=1..4}=1 :- X=1..4, Y=1..4.
cage(X1,Y1,X2,Y2):- solution(X1,Y1,_), solution(X2,Y2,_), ((X1-1)/subgrid_size)==((X2-1)/subgrid_size), ((Y1-1)/subgrid_size)==((Y2-1)/subgrid_size).

:- solution(X,Y1,N), solution(X,Y2,N), Y1 != Y2.
:- solution(X1,Y,N), solution(X2,Y,N), X1 != X2.
:- cage(X1,Y1,X2,Y2), solution(X1,Y1,N), solution(X2,Y2,N), X1!=X2, Y1!=Y2.

#show solution/3.
