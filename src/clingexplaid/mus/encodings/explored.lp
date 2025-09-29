% EXPLORED ENCODING
% -----------------
% sat(ID,A).    : Found satisifable subsets
% unsat(ID,A).  : Found unsatisfiable subsets
% test(A).      : Tested subset

% Check that test is not subset of any sat
explored(sat) :- sat(S,_), OVERLAP=#count{A: sat(S,A), test(A)}, TEST_SIZE=#count{A: test(A)}, OVERLAP==TEST_SIZE.
% Check that test in not superset of any unsat
explored(unsat) :- unsat(U,_), OVERLAP=#count{A: unsat(U,A), test(A)}, UNSAT_SIZE=#count{A: unsat(S,A)}, OVERLAP==UNSAT_SIZE.
