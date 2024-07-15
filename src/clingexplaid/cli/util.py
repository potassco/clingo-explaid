from dataclasses import dataclass
from typing import Set, Tuple

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

    def __str__(self):
        return f"<Model {self.model_id}: [{", ".join([str(atom) for atom in self.atoms])}]>"

    __repr__ = __str__
