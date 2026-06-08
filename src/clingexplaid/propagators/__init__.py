"""
Propagators for Explanation
"""

# pragma: no cover

from .propagator_solver_decisions import SolverDecisionPropagator

DecisionLevel = list[int]
DecisionLevelList = list[DecisionLevel]

__all__ = [
    "SolverDecisionPropagator",
]
