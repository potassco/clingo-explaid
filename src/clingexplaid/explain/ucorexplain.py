import base64
import os
from typing import List

import clingo
from clingo.script import enable_python
from clingraph.clingo_utils import ClingraphContext, add_elements_ids, add_svg_interaction
from clingraph.graphviz import compute_graphs, render
from clingraph.orm import Factbase
from dumbo_asp.primitives.models import Model as DumboModel
from dumbo_asp.primitives.programs import SymbolicProgram
from dumbo_asp.primitives.rules import SymbolicRule

from .constants import ENCODINGS_PATH


def path(file: str) -> str:
    import pathlib

    directory = pathlib.Path(__file__).parent.resolve() / ".."
    return str(directory / file)


def file_to_str(file: str) -> str:
    with open(path(file)) as f:
        return f.read()


def program_from_files(files: List[str]) -> SymbolicProgram:
    return SymbolicProgram.parse("\n".join(file_to_str(file) for file in files))


def rule_to_base64(rule_str: str):
    s = str(rule_str).strip('"')
    r = SymbolicRule.parse(s)
    r = r.with_chopped_body(with_backward_search=True, backward_search_symbols=(";", " :-"))
    encoded = base64.b64encode(str(r).encode("ascii"))
    return encoded


def save_graph(graph: DumboModel):
    with open("graph.lp", "wb") as file_to_save:
        for a in graph:

            if a.predicate_name == "node":
                if str(a.arguments[0]).strip('"') == "None":
                    continue
                file_to_save.write(a.predicate_name.encode())
                file_to_save.write("({}".format(",".join([str(a).strip('"') for a in a.arguments[:-1]])).encode())
                t = a.arguments[-1].arguments
                file_to_save.write(", (".encode())
                file_to_save.write(str(t[0]).encode())
                if len(t) > 1:
                    file_to_save.write(', "'.encode())
                    s = rule_to_base64(str(t[1]))
                    file_to_save.write(s)
                    file_to_save.write('"'.encode())
                    if len(t) == 3:
                        file_to_save.write(",".encode())
                        file_to_save.write(str(t[2]).encode())
                file_to_save.write(")".encode())
            if a.predicate_name == "link":
                if str(a.arguments[1]).strip('"') == "None":
                    continue
                file_to_save.write(a.predicate_name.encode())
                file_to_save.write("({}".format(",".join([str(a).strip('"') for a in a.arguments[:-1]])).encode())
                s = rule_to_base64(str(a.arguments[-1]))
                file_to_save.write(', "'.encode())
                file_to_save.write(s)
                file_to_save.write('"'.encode())

            file_to_save.write(").\n".encode())


def visualize(file_path, tree: bool = False, create_image: bool = True) -> Factbase:
    fb = Factbase(prefix="viz_")
    ctl = clingo.Control(["--warn=none"])
    ctx = ClingraphContext()
    add_elements_ids(ctl)
    ctl.load(file_path)
    if tree:
        ctl.load(os.path.join(ENCODINGS_PATH, "clingraph_tree.lp"))
    else:
        ctl.load(os.path.join(ENCODINGS_PATH, "clingraph_simple.lp"))
    enable_python()

    ctl.ground([("base", [])], context=ctx)
    ctl.solve(on_model=fb.add_model)
    graphs = compute_graphs(fb, graphviz_type="digraph")
    if create_image:
        path_png = render(graphs, format="png")
        print("PNG Image saved in: " + path_png["default"])
        paths = render(graphs, view=True, format="svg")
        add_svg_interaction([paths])
        print(
            "SVG Image saved in: "
            + paths["default"]
            + "      Click on the nodes to expand! If your browser is opening empty, you might have to scroll to the "
            "side to find the first node"
        )
    return fb
