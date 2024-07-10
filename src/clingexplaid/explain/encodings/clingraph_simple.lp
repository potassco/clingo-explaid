
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

viz_node(X):-node(X,_,_).
viz_attr(node,X, style, filled):-node(X,_,_).
viz_attr(node,X, shape, plain):-node(X,_,_).
viz_attr(node, X, fillcolor, red):-node(X,false,_).
viz_attr(node, X, fillcolor, green):-node(X,true,_), not fact(X), not node(X,_,(assumption)).
viz_attr(node, X, fillcolor, fact):-node(X,true,_), fact(X), not node(X,_,(assumption)).
viz_attr(node, X, fillcolor, assumption_color):-node(X,true,_), node(X,_,(assumption)).
viz_attr(node, X, label, @concat(
    "<<TABLE cellborder='1' cellspacing='0'>",
    "<TR><TD><b>{{name}}</b></TD></TR>",
    "<TR><TD><i>{{reason}} </i><br/>",
        "<FONT face='monospace' point-size='10'>{{rule}} </FONT></TD></TR>",
    "</TABLE>>")):-node(X,_,_).
viz_attr(node, X, (label,reason), R):-node_reason(X,R).
viz_attr(node, X, (label,rule),@decodeB64(R)):-node_rule(X,R).
viz_attr(node, X, (label,name), X):-node(X,_,_).
viz_edge((X,Y)):-link(X,Y,_),X!=Y.
viz_attr(edge,(X,Y),arrowhead,vee):-link(X,Y,R),X!=Y.
viz_attr(edge,(X,Y),arrowsize,"0.5"):-link(X,Y,R),X!=Y.
viz_attr(edge,(X,Y),label,"<<FONT face='monospace'>{{rule}}</FONT>>"):-link(X,Y,R),X!=Y, not node_rule(X,R).
viz_attr(edge,(X,Y),(label,rule), @decodeB64(R)):-link(X,Y,R),X!=Y, not node_rule(X,R).


% SVG interaction
viz_attr(edge,E,id, E):-viz_edge(E).
viz_attr(node,X, id, X):-node(X,_,_).
linked_element(node,Y,X):-link(X,Y,_).
linked_element(node,X,X):-node(X,_,_).
linked_element(edge,(X,Y),X):-link(X,Y,_),viz_edge((X,Y)).

root(X):- node(X,_,_), #count{Y: node(Y,_,_), link(Y,X,_), Y!=X}=0.
viz_attr(node,X,class,@svg_init("visibility","hidden")):-node(X,_,_), not root(X).
viz_attr(edge,E,class,@svg_init("visibility","hidden")):-viz_edge(E).

viz_attr(Type,E,class,@svg("click",X,"visibility","visible")):-linked_element(Type,E,X).
viz_attr(Type,E,class,@svg("mouseenter",X,"opacity","1")):-linked_element(Type,E,X).
viz_attr(Type,E,class,@svg("mouseleave",X,"opacity","0.3")):-linked_element(Type,E,X).
