"""The audit: perturb a case, re-explain, and score what survived.

The headline metric is the *paradox rate*: the fraction of
perturbations where the answer stayed the same but the explanation
changed. An explanation that flips while its answer holds cannot be
the real reason for the answer — it is a story told after the fact.
The audit also attributes every break: per claim, which perturbation
broke it, and per case, which perturbation broke the most claims.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List, Sequence

from .explainers import AGENTS, explain
from .models import (
    EXPECTED_CHANGE_KINDS,
    SEMANTIC_PRESERVING_KINDS,
    AgentSummary,
    Case,
    CaseAudit,
    ClaimStability,
    Explanation,
    PerturbationKind,
    verdict_for,
)
from .perturbations import apply_perturbation

# Seeds per perturbation kind. Reorder and typo noise are stochastic,
# so they get three seeds each; the rest are deterministic functions
# of the case and need one.
SEEDS: Dict[PerturbationKind, List[int]] = {
    PerturbationKind.REORDER_EVIDENCE: [1, 2, 3],
    PerturbationKind.TYPO_NOISE: [1, 2, 3],
}
DEFAULT_SEEDS = [1]


def seeds_for(kind: PerturbationKind) -> List[int]:
    return SEEDS.get(kind, DEFAULT_SEEDS)


def jaccard(a: frozenset, b: frozenset) -> float:
    """Claim-set similarity; two empty explanations agree perfectly."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def confidence_drift(baseline: Explanation, perturbed: Explanation) -> float:
    """Mean |delta confidence| over claims matched by evidence id."""
    base = baseline.claim_by_evidence()
    pert = perturbed.claim_by_evidence()
    shared = [ev_id for ev_id in base if ev_id in pert]
    if not shared:
        return 0.0
    total = sum(abs(base[e].confidence - pert[e].confidence) for e in shared)
    return total / len(shared)


def audit_case(case: Case, agent: str) -> CaseAudit:
    """Audit one case under one agent across all perturbations."""
    baseline = explain(case, agent)
    base_keys = baseline.claim_keys()
    runs = []  # (kind, answer_ok, jaccard, paradox, drift, missing, added)
    for kind in PerturbationKind:
        for seed in seeds_for(kind):
            perturbed_case = apply_perturbation(case, kind, seed)
            perturbed = explain(perturbed_case, agent)
            pert_keys = perturbed.claim_keys()
            sim = jaccard(base_keys, pert_keys)
            answer_ok = perturbed.answer == baseline.answer
            paradox = answer_ok and sim < 1.0
            drift = confidence_drift(baseline, perturbed)
            runs.append((kind, answer_ok, sim, paradox, drift,
                         base_keys - pert_keys, pert_keys - base_keys))

    n = len(runs)
    answer_stability = sum(1 for r in runs if r[1]) / n
    explanation_stability = sum(r[2] for r in runs) / n
    paradox_rate = sum(1 for r in runs if r[3]) / n
    semantic = [r for r in runs if r[0] in SEMANTIC_PRESERVING_KINDS]
    paradox_semantic = (
        sum(1 for r in semantic if r[3]) / len(semantic) if semantic else 0.0
    )
    mean_drift = sum(r[4] for r in runs) / n

    # Per-claim survival and breakers. broken_by stores, per kind, the
    # *rate* of runs of that kind in which the claim was absent, so
    # kinds with three seeds are not weighted 3x over kinds with one.
    claim_stability: List[ClaimStability] = []
    runs_by_kind: Dict[str, int] = {}
    for kind, _ok, _sim, _par, _drift, _missing, _added in runs:
        runs_by_kind[kind.value] = runs_by_kind.get(kind.value, 0) + 1
    for claim in baseline.claims:
        key = claim.key()
        missing_by_kind: Dict[str, int] = defaultdict(int)
        survived = 0
        for kind, _ok, _sim, _par, _drift, missing, _added in runs:
            if key in missing:
                missing_by_kind[kind.value] += 1
            else:
                survived += 1
        broken_by = {
            k: v / runs_by_kind[k] for k, v in missing_by_kind.items()
        }
        claim_stability.append(ClaimStability(
            key, claim.text, list(claim.evidence_ids),
            survived / n if n else 1.0, broken_by,
        ))

    # Case breaker: the semantic-preserving kind with the highest mean
    # claim-set change (lost + added claims) per run. Expected-change
    # kinds are excluded: they are supposed to change the explanation.
    # Added claims matter too (e.g. the confident agent citing the
    # injected passage) — without them, injection would look harmless.
    mean_change: Dict[str, float] = {}
    for kind in SEMANTIC_PRESERVING_KINDS:
        kind_runs = [r for r in runs if r[0] == kind]
        if not kind_runs:
            continue
        mean_change[kind.value] = sum(
            len(r[5]) + len(r[6]) for r in kind_runs) / len(kind_runs)
    breaker = None
    if mean_change and max(mean_change.values()) > 0:
        breaker = max(sorted(mean_change), key=lambda k: mean_change[k])

    # Per-kind aggregates.
    per_kind: Dict[str, Dict[str, float]] = {}
    for kind in PerturbationKind:
        kind_runs = [r for r in runs if r[0] == kind]
        m = len(kind_runs)
        per_kind[kind.value] = {
            "paradox_rate": sum(1 for r in kind_runs if r[3]) / m,
            "answer_stability": sum(1 for r in kind_runs if r[1]) / m,
            "explanation_stability": sum(r[2] for r in kind_runs) / m,
        }

    min_claim = min((c.survival_rate for c in claim_stability), default=1.0)
    # The verdict judges semantic-preserving perturbations only: a flip
    # under drop_weak_evidence or truncate_evidence is honest
    # sensitivity (the evidence changed), never instability.
    verdict = verdict_for(paradox_semantic, min_claim, answer_stability)
    return CaseAudit(
        case_id=case.case_id,
        domain=case.domain,
        agent=agent,
        baseline_answer=baseline.answer,
        gold_answer=case.gold_answer,
        answer_stable=baseline.answer == case.gold_answer,
        answer_stability=answer_stability,
        explanation_stability=explanation_stability,
        paradox_rate=paradox_rate,
        paradox_rate_semantic=paradox_semantic,
        mean_confidence_drift=mean_drift,
        claim_stability=claim_stability,
        verdict=verdict,
        breaker=breaker,
        per_kind=per_kind,
    )


def audit_all(cases: Sequence[Case], agents: Sequence[str] = AGENTS
              ) -> List[CaseAudit]:
    """Audit every case under every agent."""
    out: List[CaseAudit] = []
    for case in cases:
        for agent in agents:
            out.append(audit_case(case, agent))
    return out


def summarize(agent: str, audits: Sequence[CaseAudit]) -> AgentSummary:
    """Aggregate one agent's case audits into a summary."""
    mine = [a for a in audits if a.agent == agent]
    n = len(mine)
    if n == 0:
        return AgentSummary(agent, 0, 0.0, 0.0, 0.0, 0.0, 0.0, {}, {}, [])
    mean = lambda f: sum(f(a) for a in mine) / n
    verdict_counts = dict(Counter(a.verdict for a in mine))
    per_kind: Dict[str, float] = {}
    for kind in PerturbationKind:
        per_kind[kind.value] = mean(lambda a, k=kind: a.per_kind[k.value]["paradox_rate"])
    worst = sorted(mine, key=lambda a: (-a.paradox_rate, a.case_id))[:5]
    return AgentSummary(
        agent=agent,
        n_cases=n,
        mean_paradox_rate=mean(lambda a: a.paradox_rate),
        mean_paradox_rate_semantic=mean(lambda a: a.paradox_rate_semantic),
        mean_answer_stability=mean(lambda a: a.answer_stability),
        mean_explanation_stability=mean(lambda a: a.explanation_stability),
        mean_confidence_drift=mean(lambda a: a.mean_confidence_drift),
        verdict_counts=verdict_counts,
        per_kind_paradox=per_kind,
        worst_cases=[a.case_id for a in worst],
    )


def expected_change_paradox(audits: Sequence[CaseAudit]) -> Dict[str, float]:
    """Paradox rate restricted to expected-change kinds, per agent.

    A paradox under drop_weak_evidence or truncate_evidence is honest
    sensitivity (the evidence changed), so it is reported separately
    and never counted against the agent's semantic paradox rate.
    """
    out: Dict[str, float] = {}
    for agent in AGENTS:
        mine = [a for a in audits if a.agent == agent]
        if not mine:
            continue
        vals = []
        for a in mine:
            rates = [a.per_kind[k.value]["paradox_rate"]
                     for k in EXPECTED_CHANGE_KINDS]
            vals.append(sum(rates) / len(rates))
        out[agent] = sum(vals) / len(vals)
    return out
