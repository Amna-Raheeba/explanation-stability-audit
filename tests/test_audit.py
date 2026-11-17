"""Tests for the audit engine: metrics, verdicts, attribution."""

import pytest

from explanation_stability_audit.audit import (
    audit_all,
    audit_case,
    confidence_drift,
    expected_change_paradox,
    jaccard,
    summarize,
)
from explanation_stability_audit.evaluation import load_cases
from explanation_stability_audit.explainers import explain
from explanation_stability_audit.models import (
    Case,
    Claim,
    Evidence,
    Explanation,
    PerturbationKind,
)


def _case() -> Case:
    return Case(
        "T-01", "health", "Should patient Aisha be escalated to urgent care?",
        [
            Evidence("H1", "Temperature 39.2C. This is a high fever for "
                     "patient Aisha, and the risk is severe.",
                     "escalate", 2.0, 0.9),
            Evidence("H2", "Urgent care review: heart rate 124 bpm. "
                     "Patient Aisha has a high heart rate.",
                     "escalate", 2.0, 0.9),
            Evidence("H3", "Patient Aisha feels slightly better today. "
                     "The patient feels better.", "routine", 0.5, 0.6),
            Evidence("H4", "Patient Aisha has a history of asthma. "
                     "Asthma should be monitored for patient Aisha.",
                     "monitor", 1.0, 0.7),
            Evidence("H5", "Patient Aisha slept well. The patient slept "
                     "well and feels rested.", "routine", 0.5, 0.6),
        ],
        "escalate",
    )


def test_jaccard_edge_cases():
    assert jaccard(frozenset(), frozenset()) == 1.0
    assert jaccard(frozenset({"a"}), frozenset()) == 0.0
    assert jaccard(frozenset({"a", "b"}), frozenset({"b", "c"})) == pytest.approx(1 / 3)


def test_confidence_drift_matches_shared_claims_only():
    base = Explanation("yes", [
        Claim("a", ["E1"], 0.9, stance="yes"),
        Claim("b", ["E2"], 0.8, stance="yes"),
    ])
    pert = Explanation("yes", [
        Claim("a", ["E1"], 0.7, stance="yes"),
        Claim("c", ["E3"], 0.5, stance="yes"),
    ])
    assert confidence_drift(base, pert) == pytest.approx(0.2)
    assert confidence_drift(base, Explanation("yes", [])) == 0.0


def test_audit_case_stable_agent_is_stable():
    audit = audit_case(_case(), "stable")
    assert audit.verdict == "stable"
    assert audit.paradox_rate_semantic == 0.0
    assert audit.answer_stability == 1.0
    assert audit.baseline_answer == "escalate"
    assert audit.gold_answer == "escalate"


def test_audit_case_order_agent_breaker_is_reorder():
    audit = audit_case(_case(), "order_sensitive")
    assert audit.paradox_rate_semantic > 0.0
    assert audit.breaker == "reorder_evidence"


def test_audit_case_confident_agent_breaker_is_injection():
    audit = audit_case(_case(), "confident")
    assert audit.breaker == "irrelevant_injection"


def test_audit_case_keyword_agent_breaker_is_paraphrase():
    audit = audit_case(_case(), "keyword_fragile")
    assert audit.breaker == "paraphrase"


def test_audit_case_per_kind_covers_all_kinds():
    audit = audit_case(_case(), "stable")
    assert set(audit.per_kind) == {k.value for k in PerturbationKind}
    for row in audit.per_kind.values():
        assert set(row) == {
            "paradox_rate", "answer_stability", "explanation_stability"}


def test_audit_case_claim_stability_sums_to_baseline_claims():
    case = _case()
    audit = audit_case(case, "stable")
    assert len(audit.claim_stability) == len(explain(case, "stable").claims)
    for cs in audit.claim_stability:
        assert 0.0 <= cs.survival_rate <= 1.0
        assert cs.breaker is None or cs.breaker in {
            k.value for k in PerturbationKind}


def test_audit_all_counts():
    cases = load_cases("data/cases.json")
    audits = audit_all(cases)
    assert len(audits) == 48 * 4
    assert {a.agent for a in audits} == {
        "stable", "order_sensitive", "keyword_fragile", "confident"}


def test_summarize_stable_agent():
    cases = load_cases("data/cases.json")
    audits = audit_all(cases)
    summary = summarize("stable", audits)
    assert summary.n_cases == 48
    assert summary.mean_paradox_rate_semantic == 0.0
    assert summary.verdict_counts == {"stable": 48}
    assert len(summary.worst_cases) == 5


def test_summarize_empty():
    summary = summarize("stable", [])
    assert summary.n_cases == 0
    assert summary.mean_paradox_rate == 0.0


def test_expected_change_paradox_separate_from_semantic():
    cases = load_cases("data/cases.json")
    audits = audit_all(cases)
    expected = expected_change_paradox(audits)
    # Stable flips only under expected-change kinds (truncate/drop),
    # never under semantic ones — the split must show that.
    assert expected["stable"] > 0.0
    summary = summarize("stable", audits)
    assert summary.mean_paradox_rate_semantic == 0.0
