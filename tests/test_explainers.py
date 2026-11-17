"""Tests for the explainer agents: answers, invariants, failure modes."""

import pytest

from explanation_stability_audit.evaluation import load_cases
from explanation_stability_audit.explainers import (
    AGENTS,
    canonicalize,
    explain,
)
from explanation_stability_audit.models import PerturbationKind
from explanation_stability_audit.perturbations import apply_perturbation


def _cases():
    return load_cases("data/cases.json")


def test_agents_known():
    assert set(AGENTS) == {
        "stable", "order_sensitive", "keyword_fragile", "confident"}


def test_unknown_agent_raises():
    with pytest.raises(ValueError):
        explain(_cases()[0], "nope")


def test_stable_agent_answers_gold_on_all_cases():
    for case in _cases():
        assert explain(case, "stable").answer == case.gold_answer, case.case_id


def test_stable_agent_claims_match_gold_claims():
    for case in _cases():
        got = explain(case, "stable")
        assert got.claim_keys() == {c.key() for c in case.gold_claims}, \
            case.case_id


def test_confident_agent_answers_gold_on_all_cases():
    for case in _cases():
        assert explain(case, "confident").answer == case.gold_answer, \
            case.case_id


def test_confident_agent_cites_every_passage_at_095():
    for case in _cases():
        exp = explain(case, "confident")
        assert len(exp.claims) == len(case.evidence)
        assert all(c.confidence == 0.95 for c in exp.claims)


def test_keyword_agent_never_empty_baseline():
    for case in _cases():
        assert explain(case, "keyword_fragile").claims, case.case_id


def test_keyword_agent_confidence_responds_to_match_quality():
    case = _cases()[0]
    base = explain(case, "keyword_fragile")
    paraphrased = apply_perturbation(case, PerturbationKind.PARAPHRASE, 1)
    pert = explain(paraphrased, "keyword_fragile")
    base_conf = [c.confidence for c in base.claims]
    pert_conf = [c.confidence for c in pert.claims]
    # Paraphrase thins the match, so some surviving claim loses confidence.
    assert pert_conf != base_conf or len(pert_conf) != len(base_conf)


def test_stable_agent_invariant_under_semantic_perturbations():
    for case in _cases():
        base = explain(case, "stable")
        for kind in (PerturbationKind.REPEAT_QUERY,
                     PerturbationKind.PARAPHRASE,
                     PerturbationKind.SYNONYM_SWAP,
                     PerturbationKind.REORDER_EVIDENCE,
                     PerturbationKind.TYPO_NOISE,
                     PerturbationKind.IRRELEVANT_INJECTION):
            for seed in (1, 2, 3):
                pert = explain(apply_perturbation(case, kind, seed), "stable")
                assert pert.answer == base.answer, (case.case_id, kind)
                assert pert.claim_keys() == base.claim_keys(), \
                    (case.case_id, kind, seed)


def test_order_agent_changes_under_reorder_somewhere():
    changed = 0
    for case in _cases():
        base = explain(case, "order_sensitive")
        for seed in (1, 2, 3):
            pert = explain(apply_perturbation(
                case, PerturbationKind.REORDER_EVIDENCE, seed),
                "order_sensitive")
            if pert.claim_keys() != base.claim_keys():
                changed += 1
                break
    assert changed > 30  # most cases must flip under reorder


def test_confident_agent_cites_injected_passage():
    for case in _cases():
        injected = apply_perturbation(
            case, PerturbationKind.IRRELEVANT_INJECTION, 1)
        exp = explain(injected, "confident")
        assert any("X1" in c.evidence_ids for c in exp.claims), case.case_id


def test_stable_agent_ignores_injected_passage():
    for case in _cases():
        injected = apply_perturbation(
            case, PerturbationKind.IRRELEVANT_INJECTION, 1)
        assert explain(injected, "stable").claim_keys() == \
            explain(case, "stable").claim_keys(), case.case_id


def test_canonicalize_maps_synonym_pairs_together():
    assert canonicalize("risk danger") == "danger danger"
    assert canonicalize("patient person") == "patient patient"
    assert canonicalize("high temperature") == "elevated heat"
