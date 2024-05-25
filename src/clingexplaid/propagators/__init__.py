"""
Propagators for Explanation
"""

# pragma: no cover

from typing import List

from .propagator_decision_order import DecisionOrderPropagator
from .propagator_solver_decisions import SolverDecisionPropagator

DecisionLevel = List[int]
DecisionLevelList = List[DecisionLevel]

__all__ = [
    "DecisionOrderPropagator",
    "SolverDecisionPropagator",
]
