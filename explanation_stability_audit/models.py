"""Data model: cases, evidence, explanations, and audit results.

A case is a question plus a small set of evidence passages. Each
passage states which answer it supports and with what weight, so a
deterministic explainer agent can derive both an answer (the
best-supported label) and an explanation (one claim per supporting
passage) without any model call. The audit then perturbs the case and
checks whether the explanation survives while the answer holds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class PerturbationKind(str, Enum):
    """The eight perturbations the audit applies to a case."""

    REPEAT_QUERY = "repeat_query"
    PARAPHRASE = "paraphrase"
    SYNONYM_SWAP = "synonym_swap"
    REORDER_EVIDENCE = "reorder_evidence"
    TYPO_NOISE = "typo_noise"
    IRRELEVANT_INJECTION = "irrelevant_injection"
    DROP_WEAK_EVIDENCE = "drop_weak_evidence"
    TRUNCATE_EVIDENCE = "truncate_evidence"

    @property
    def label(self) -> str:
        return {
            PerturbationKind.REPEAT_QUERY: "Repeat query (control)",
            PerturbationKind.PARAPHRASE: "Paraphrase question",
            PerturbationKind.SYNONYM_SWAP: "Synonym swap in evidence",
            PerturbationKind.REORDER_EVIDENCE: "Reorder evidence",
            PerturbationKind.TYPO_NOISE: "Typo noise in question",
            PerturbationKind.IRRELEVANT_INJECTION: "Inject irrelevant passage",
            PerturbationKind.DROP_WEAK_EVIDENCE: "Drop weakest evidence",
            PerturbationKind.TRUNCATE_EVIDENCE: "Truncate evidence text",
        }[self]


# Perturbations that are *expected* to change the explanation: the
# evidence itself changed, so a claim disappearing is honest
# sensitivity, not instability. Everything else must leave the
# explanation alone.
EXPECTED_CHANGE_KINDS = frozenset(
    {
        PerturbationKind.DROP_WEAK_EVIDENCE,
        PerturbationKind.TRUNCATE_EVIDENCE,
    }
)

# Perturbations that must not change anything at all: the input is
# semantically identical, so any flip is pure instability.
SEMANTIC_PRESERVING_KINDS = frozenset(
    {
        PerturbationKind.REPEAT_QUERY,
        PerturbationKind.PARAPHRASE,
        PerturbationKind.SYNONYM_SWAP,
        PerturbationKind.REORDER_EVIDENCE,
        PerturbationKind.TYPO_NOISE,
        PerturbationKind.IRRELEVANT_INJECTION,
    }
)


@dataclass(frozen=True)
class Evidence:
    """One passage the agent may cite.

    ``supports`` is the answer label this passage argues for and
    ``weight`` is how strongly. ``strength`` (0..1) is the passage's
    own reliability, used for confidence, not for the answer.
    """

    id: str
    text: str
    supports: str
    weight: float
    strength: float = 0.8

    def truncated(self) -> "Evidence":
        """First sentence only, for the truncate_evidence perturbation."""
        first = self.text.split(". ")[0]
        if not first.endswith("."):
            first += "."
        return Evidence(self.id, first, self.supports, self.weight, self.strength)


@dataclass(frozen=True)
class Claim:
    """One reason in an explanation: text + cited evidence + confidence.

    ``stance`` is the answer label this claim argues for. A claim's
    identity is (stance, cited evidence): two explanations that cite
    the same passages for the same answer state the same reasons,
    even if the quoted words differ. The quote is illustration, not
    identity — otherwise a synonym swap would count as a changed
    reason when only the wording changed.
    """

    text: str
    evidence_ids: List[str]
    confidence: float
    stance: str = ""

    def key(self) -> str:
        """Identity of a claim for stability matching."""
        return "%s|%s" % (self.stance, ",".join(sorted(self.evidence_ids)))


@dataclass(frozen=True)
class Explanation:
    """An agent's answer plus the claims that supposedly justify it."""

    answer: str
    claims: List[Claim]

    def claim_keys(self) -> frozenset:
        return frozenset(c.key() for c in self.claims)

    def claim_by_evidence(self) -> Dict[str, Claim]:
        """First claim citing each evidence id (claims cite one id here)."""
        out: Dict[str, Claim] = {}
        for claim in self.claims:
            for ev_id in claim.evidence_ids:
                out.setdefault(ev_id, claim)
        return out


@dataclass(frozen=True)
class Case:
    """One audit case: a question, its evidence, and the gold answer."""

    case_id: str
    domain: str
    question: str
    evidence: List[Evidence]
    gold_answer: str
    gold_claims: List[Claim] = field(default_factory=list)

    def evidence_by_id(self) -> Dict[str, Evidence]:
        return {ev.id: ev for ev in self.evidence}


@dataclass(frozen=True)
class ClaimStability:
    """How one baseline claim survived the perturbations."""

    claim_key: str
    claim_text: str
    evidence_ids: List[str]
    survival_rate: float
    broken_by: Dict[str, float] = field(default_factory=dict)

    @property
    def breaker(self) -> Optional[str]:
        """The perturbation kind that broke this claim most often.

        Rates, not counts: kinds with three seeds are not weighted 3x
        over kinds with one. Ties break alphabetically (deterministic).
        """
        if not self.broken_by:
            return None
        return max(sorted(self.broken_by), key=lambda k: self.broken_by[k])


@dataclass(frozen=True)
class CaseAudit:
    """The full audit of one case under one agent."""

    case_id: str
    domain: str
    agent: str
    baseline_answer: str
    gold_answer: str
    answer_stable: bool
    answer_stability: float
    explanation_stability: float
    paradox_rate: float
    paradox_rate_semantic: float
    mean_confidence_drift: float
    claim_stability: List[ClaimStability]
    verdict: str
    breaker: Optional[str]
    per_kind: Dict[str, Dict[str, float]] = field(default_factory=dict)

    @property
    def min_claim_stability(self) -> float:
        if not self.claim_stability:
            return 1.0
        return min(c.survival_rate for c in self.claim_stability)


@dataclass(frozen=True)
class AgentSummary:
    """Aggregate audit numbers for one agent over all cases."""

    agent: str
    n_cases: int
    mean_paradox_rate: float
    mean_paradox_rate_semantic: float
    mean_answer_stability: float
    mean_explanation_stability: float
    mean_confidence_drift: float
    verdict_counts: Dict[str, int]
    per_kind_paradox: Dict[str, float]
    worst_cases: List[str]


def normalize_text(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    kept = []
    for ch in text.lower():
        if ch.isalnum() or ch.isspace():
            kept.append(ch)
        else:
            kept.append(" ")
    return " ".join("".join(kept).split())


def verdict_for(paradox_rate: float, min_claim_stability: float,
                answer_stability: float) -> str:
    """stable / fragile / unstable, from the audit numbers."""
    if answer_stability < 0.5:
        return "unstable"
    if paradox_rate == 0.0 and min_claim_stability >= 0.8:
        return "stable"
    if paradox_rate < 0.5:
        return "fragile"
    return "unstable"
