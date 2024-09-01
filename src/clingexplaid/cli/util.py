from dataclasses import dataclass
from typing import Iterable, Optional, Set, Tuple

import clingo


@dataclass
class Atom:
    grounder_literal: int
    solver_literal: int
    symbol: clingo.Symbol
    shown: bool

    def __str__(self):
        return f"<Atom {str(self.symbol)}>"

    def __hash__(self):
        return hash(self.__key())

    def __key(self) -> Tuple[int, int, clingo.Symbol]:
        return self.grounder_literal, self.solver_literal, self.symbol

    __repr__ = __str__


@dataclass
class StableModel:
    model_id: int
    atoms: Set[Atom]
    cost: Optional[Iterable[int]] = None
    optimal: bool = False

    def __init__(self, model_id: int, model: clingo.Model, cost: Optional[Iterable[int]] = None, optimal: bool = False):
        self.model_id = model_id
        self.cost = cost if cost else None
        self.optimal = optimal
        self.atoms = set()
        for symbol in model.symbols(atoms=True):
            atom = Atom(42, 42, symbol, True)  # TODO: Fix this
            self.atoms.add(atom)

    def __hash__(self):
        return hash((self.model_id, "_".join([str(a.symbol) for a in self.atoms])))

    def __str__(self):
        return f"<Model {self.model_id}: [{", ".join([str(atom) for atom in self.atoms])}]>"

    __repr__ = __str__

    def get_facts_string(self):
        out = []
        for atom in self.atoms:
            out.append(f"{str(atom.symbol)}.")
        return " ".join(out)
