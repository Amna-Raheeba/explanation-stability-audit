"""Evaluation: load the case set, audit every agent, summarize."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from .audit import audit_all, expected_change_paradox, summarize
from .explainers import AGENTS
from .models import (
    AgentSummary,
    Case,
    CaseAudit,
    Claim,
    Evidence,
)


def load_cases(path: str | Path) -> List[Case]:
    """Load cases from a JSON file (see scripts/build_cases.py)."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = []
    for item in raw:
        evidence = [Evidence(**ev) for ev in item["evidence"]]
        gold_claims = [Claim(**c) for c in item.get("gold_claims", [])]
        cases.append(Case(
            item["case_id"], item["domain"], item["question"], evidence,
            item["gold_answer"], gold_claims,
        ))
    return cases


def evaluate(cases: Sequence[Case], agents: Sequence[str] = AGENTS
             ) -> Tuple[List[CaseAudit], Dict[str, AgentSummary], Dict[str, float]]:
    """Run the full audit and return (case audits, summaries, headline)."""
    audits = audit_all(cases, agents)
    summaries = {a: summarize(a, audits) for a in agents}
    expected = expected_change_paradox(audits)
    headline: Dict[str, float] = {}
    for agent in agents:
        s = summaries[agent]
        headline["%s_paradox_rate" % agent] = s.mean_paradox_rate
        headline["%s_paradox_rate_semantic" % agent] = s.mean_paradox_rate_semantic
        headline["%s_answer_stability" % agent] = s.mean_answer_stability
        headline["%s_explanation_stability" % agent] = s.mean_explanation_stability
        headline["%s_confidence_drift" % agent] = s.mean_confidence_drift
        headline["%s_expected_change_paradox" % agent] = expected.get(agent, 0.0)
    # The headline gap: the paradox rate of the most fragile agent
    # minus the stable agent's. A large gap means the metric separates.
    fragile = max(agents, key=lambda a: summaries[a].mean_paradox_rate_semantic)
    headline["paradox_gap"] = (
        summaries[fragile].mean_paradox_rate_semantic
        - summaries["stable"].mean_paradox_rate_semantic
    )
    headline["n_cases"] = float(len(cases))
    headline["n_audits"] = float(len(audits))
    return audits, summaries, headline


def default_cases_path() -> Path:
    """data/cases.json next to the package directory."""
    return Path(__file__).resolve().parent.parent / "data" / "cases.json"
