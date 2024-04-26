#program base.
#const subgrid_size = 2.
solution(X,Y,V) :- initial(X,Y,V).
1 = { solution(X,Y,N): N = (1..4) } :- X = (1..4); Y = (1..4).
cage(X1,Y1,X2,Y2) :- solution(X1,Y1,_); solution(X2,Y2,_); ((X1-1)/subgrid_size) = ((X2-1)/subgrid_size); ((Y1-1)/subgrid_size) = ((Y2-1)/subgrid_size).
#false :- solution(X,Y1,N); solution(X,Y2,N); Y1 != Y2.
#false :- solution(X1,Y,N); solution(X2,Y,N); X1 != X2.
#false :- cage(X1,Y1,X2,Y2); solution(X1,Y1,N); solution(X2,Y2,N); X1 != X2; Y1 != Y2.
#show solution/3.
#program base.
%{ initial(1,1,4) }.
%{ initial(4,1,4) }.
%{ initial(1,4,2) }.
%{ initial(2,3,3) }.
%{ initial(3,3,1) }.
%{ initial(3,4,3) }.
#show _muc/1.
#show _assumption/1.
_assumption(initial(1,1,4)).
_muc(initial(1,1,4)) :- initial(1,1,4).
_assumption(initial(4,1,4)).
_muc(initial(4,1,4)) :- initial(4,1,4).
_assumption(initial(1,4,2)).
_muc(initial(1,4,2)) :- initial(1,4,2).
_assumption(initial(2,3,3)).
_muc(initial(2,3,3)) :- initial(2,3,3).
_assumption(initial(3,3,1)).
_muc(initial(3,3,1)) :- initial(3,3,1).
_assumption(initial(3,4,3)).
_muc(initial(3,4,3)) :- initial(3,4,3).
#show initial/3.
