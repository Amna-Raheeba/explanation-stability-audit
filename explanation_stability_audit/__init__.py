"""Explanation Stability Audit: does an agent's explanation survive
perturbations that leave its answer unchanged? If the reasons flip
while the answer holds, the explanation is not the real reason.
"""

__version__ = "0.1.0"

from .audit import audit_all, audit_case, summarize
from .evaluation import evaluate, load_cases
from .explainers import AGENTS, explain
from .models import Case, Claim, Evidence, Explanation, PerturbationKind
from .perturbations import apply_perturbation

__all__ = [
    "AGENTS",
    "Case",
    "Claim",
    "Evidence",
    "Explanation",
    "PerturbationKind",
    "apply_perturbation",
    "audit_all",
    "audit_case",
    "evaluate",
    "explain",
    "load_cases",
    "summarize",
]
