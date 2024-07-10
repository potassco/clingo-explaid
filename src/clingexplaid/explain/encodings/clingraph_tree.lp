
#script (python)
from clingo.symbol import String
import base64

def decodeB64(s):
    s = str(s)
    decoded = base64.b64decode(s).decode('ascii')
    return String(decoded)

#end.

fact(X):-node(X,_,_), #false: link(X,Y,_), Y!=X.

node_rule(X,R):-node(X,_,(_,R,_)).
node_rule(X,R):-node(X,_,(_,R)).
node_rule(X,""):-node(X,_,(_)), not node(X,_,(_,_)), not node(X,_,(_,_,_)).

node_reason(X,"Support"):-node(X,_,(support,_)), not fact(X).
node_reason(X,"Fact"):-node(X,_,(support,_)), fact(X).
node_reason(X,"Assumption"):-node(X,_,(assumption)).
node_reason(X,"Uper bound was already reacheded"):-node(X,_,(head_upper_bound,_)).
node_reason(X,"No rule can support"):-node(X,_,(lack_of_support,)).
node_reason(X,"No rule can support"):-node(X,_,(lack_of_support)).
node_reason(X,@concat("No other rule can support ", A)):-node(X,_,(last_support,_,A)).
node_reason(X,"Avoid satisfing constraint"):-node(X,_,(constraint,_,_)).

#const red = "#F6B0B0".
#const green = "#BFFEBF".
#const fact = "#609E60".
#const assumption_color = "#AAFDD8".

root(X):- node(X,_,_), #count{Y: node(Y,_,_), link(Y,X,_), Y!=X}=0.
node_main((X,root)):-root(X).
node_main((X,Y)):-node(X,_,_), link(Y,X,_), #false: link(Z,X,_), Z>Y.
node_main((X,Y)):-node(X,_,_), link(Y,X,_), fact(X).
all_node((X,root)):- node(X,_,_), root(X).
all_node((X,Y)):- link(Y,X,_).

viz_node(N):-all_node(N).
% viz_attr(node, N, fillcolor, blue):-all_node(N), node_main(N).


% viz_node(X):-node(X,_,_).
viz_attr(node,N, style, filled):-all_node(N).
viz_attr(node,N, shape, plain):-all_node(N).
viz_attr(node, (X,Y), fillcolor, red):-node(X,false,_), all_node((X,Y)).
viz_attr(node, (X,Y), fillcolor, green):-node(X,true,_), all_node((X,Y)), not fact(X).
viz_attr(node, (X,Y), fillcolor, fact):-node(X,true,_), all_node((X,Y)), fact(X), not node(X,_,(assumption)).
viz_attr(node, (X,Y), fillcolor, assumption_color):-node(X,true,_), all_node((X,Y)), fact(X), node(X,_,(assumption)).
viz_attr(node, N, label, @concat(
    "<<TABLE cellborder='1' cellspacing='0' border='{{border}}'>",
    "<TR><TD><b>{{name}}</b></TD></TR>",
    "<TR><TD><i>{{reason}} </i><br/>",
        "<FONT face='monospace' point-size='10'>{{rule}} </FONT></TD></TR>",
    "</TABLE>>")):-all_node(N).
viz_attr(node, (X,Y), (label,reason), R):-node_reason(X,R),all_node((X,Y)).
viz_attr(node, (X,Y), (label,rule),@decodeB64(R)):-node_rule(X,R),all_node((X,Y)).
viz_attr(node, (X,Y), (label,name), X):-all_node((X,Y)).
viz_attr(node, N, (label,border), 2):-node_main(N).
viz_attr(node, N, (label,border), 0):-all_node(N), not node_main(N).

viz_edge((NX,NY)):-children(NX,NY).
viz_attr(edge,(NX,NY),arrowhead,vee):-viz_edge((NX,NY)).
viz_attr(edge,(NX,NY),arrowsize,"0.5"):-viz_edge((NX,NY)).
viz_attr(edge,((X,X'),(Y,Y')),label,"<<FONT face='monospace'>{{rule}}</FONT>>"):-viz_edge(((X,X'),(Y,Y'))), link(X,Y,R), not node_rule(X,R).
viz_attr(edge,((X,X'),(Y,Y')),(label,rule), @decodeB64(R)):-viz_edge(((X,X'),(Y,Y'))), not node_rule(X,R), link(X,Y,R).

children((X,X'),(Y,X)):-link(X,Y,_),X!=Y,node_main((X,X')),all_node((Y,X)).

% SVG interaction
viz_attr(edge,(X,Y),id, @concat("(",X,",",Y,")")):-viz_edge((X,Y)).
viz_attr(node,(X,Y),id, @concat("(",X,",",Y,")")):-all_node((X,Y)).
linked_element(node,NX,NY):-children(NX,NY).
linked_element(node,N,N):-all_node(N).
linked_element(T,(X,Y),N):- all_node((X,Y)), not node_main((X,Y)), node_main((X,X')), linked_element(T,(X,X'),N).
linked_element(edge,NX,(NX,NY)):-children(NX,NY),viz_edge((NX,NY)).

viz_attr(node,(X,Y),class,@svg_init("visibility","hidden")):-all_node((X,Y)), not root(X).
viz_attr(edge,E,class,@svg_init("visibility","hidden")):-viz_edge(E).

viz_attr(Type,X,class,@svg("click",E,"visibility","visible")):-linked_element(Type,E,X).
viz_attr(Type,X,class,@svg("mouseenter",E,"opacity","1")):-linked_element(Type,E,X).
viz_attr(Type,X,class,@svg("mouseleave",E,"opacity","0.3")):-linked_element(Type,E,X).

viz_attr(node,(X,X'),class,@svg("click",(X,Y),"visibility","visible")):-all_node((X,Y)), not node_main((X,Y)), node_main((X,X')).
