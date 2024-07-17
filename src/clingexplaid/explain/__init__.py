"""
Ucorexplain module for explanation workflow

authors:
    + Mario Alviano: <mario.alviano@gmail.com>
    + Susana Hahn: <susuhahnml@yahoo.com.mx>
    + Orkunt Sabuncu: <orkunt.sabuncu@potassco.com>
    + Hannes Weichelt: <mail@hweichelt.de>
"""

from typing import Iterable

from clingraph.orm import Factbase
from dumbo_asp.primitives.models import Model as DumboModel
from dumbo_asp.primitives.programs import SymbolicProgram
from dumbo_asp.queries import explanation_graph

from .constants import AUTO_EXPAND_DEPTH
from .textual import textualize_clingraph_factbase
from .ucorexplain import program_from_files, save_graph, visualize


def get_explanation_factbase(files: Iterable[str], query: str, answer_set: str, false_atoms: Iterable[str]) -> Factbase:
    query = DumboModel.of_program(query)
    answer_set = DumboModel.of_program(answer_set)
    program = program_from_files([f for f in files])
    explicitly_mentioned_atoms = DumboModel.of_program(false_atoms)

    herbrand_base = SymbolicProgram.of(
        *program,
        *SymbolicProgram.parse(answer_set.as_facts),
        *SymbolicProgram.parse(query.as_facts),
        *SymbolicProgram.parse(explicitly_mentioned_atoms.as_facts),
    ).herbrand_base

    graph = explanation_graph(
        program=program,
        answer_set=answer_set,
        herbrand_base=herbrand_base,
        query=query,
        collect_pus_program=[],
    )

    save_graph(graph)

    fb = visualize("./graph.lp", tree=True, create_image=False)
    return fb
