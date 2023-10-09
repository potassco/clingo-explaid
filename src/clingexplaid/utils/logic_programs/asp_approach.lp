% CLASSIC KRR META ENCODING :
% 	- Modified for finding all Minimal Unsatisfiable Cores of an unsatisfiable program

conjunction(B) :- literal_tuple(B),
				  hold(L): literal_tuple(B,L), L>0;
				  not hold(L): literal_tuple(B,-L), L>0.

body(normal(B)) :- rule(_,normal(B)), conjunction(B).
body(sum(B,G)) :- rule(_,sum(B,G)),
						#sum {
					   		W,L : hold(L), weighted_literal_tuple(B,L,W), L>0;
							W,L : not hold(L), weighted_literal_tuple(B,-L,W), L>0
						} >= G .

% hold(A): atom_tuple(H,A) :- rule(disjunction(H),B), body(B).
% Splitting this rule into two cases:
% 	1. the body of a rule holds but the rule has not head atoms (integrity constraint)
%		- an unsat atom containing the body of the rule is created
%	2. the body of a rule holds but the rule has at least one head atom
%		- the classic way of handeling disjunctive heads is applied (at least one of the head atoms has to be true)
unsat(B) :- rule(disjunction(H),B), body(B), not atom_tuple(H,_).
hold(A): atom_tuple(H,A) :- rule(disjunction(H),B), body(B), atom_tuple(H,_).


% modified the hold choice rule to infer choice_hold(Atom_ID)
{ choice_hold(A): atom_tuple(H,A) } :- rule(choice(H),B), body(B).
% for every choice hold infer a real hold
hold(X) :- choice_hold(X).
% add heuristic false for every choice hold (This works in experiments but might have an undiscovered edge case)
#heuristic choice_hold(_).[1,false]
:- not unsat(_).

#show.
% #show unsat/1.
% #show choice_hold/2.
#show muc(T): output(_muc(T),B), conjunction(B).

assumption_hold(T) :- output(_muc(T),B), conjunction(B).