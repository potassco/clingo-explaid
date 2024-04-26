node(1..9).

edge(1,2). edge(1,3). edge(1,4).
edge(2,1). edge(2,3).
edge(3,1). edge(3,2). edge(3,5).
edge(4,1). edge(4,5). edge(4,8).
edge(5,3). edge(5,4). edge(5,6). edge(5,8).
edge(6,5). edge(6,9).
edge(7,8).
edge(8,7). edge(8,4). edge(8,5). edge(8,9).
edge(9,6). edge(9,8).

color(red; green; blue).

% pre assignments

assign(1,green).
assign(2,blue).
assign(5,red).
assign(7,green).
