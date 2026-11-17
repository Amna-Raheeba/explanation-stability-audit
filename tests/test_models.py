"""Tests for the data model: claims, verdicts, normalization."""

import pytest

from explanation_stability_audit.models import (
    EXPECTED_CHANGE_KINDS,
    SEMANTIC_PRESERVING_KINDS,
    Claim,
    Evidence,
    Explanation,
    PerturbationKind,
    normalize_text,
    verdict_for,
)


def test_normalize_text():
    assert normalize_text("Hello,  World!") == "hello world"
    assert normalize_text("SpO2 91%") == "spo2 91"


def test_claim_key_is_stance_and_evidence_not_words():
    a = Claim("H1 supports escalate: Temperature 39.2C.", ["H1"], 0.9,
              stance="escalate")
    b = Claim("H1 supports escalate: Heat 39.2C.", ["H1"], 0.9,
              stance="escalate")
    c = Claim("H1 supports monitor: Temperature 39.2C.", ["H1"], 0.9,
              stance="monitor")
    assert a.key() == b.key()
    assert a.key() != c.key()


def test_claim_key_sorts_evidence_ids():
    a = Claim("x", ["H2", "H1"], 0.5, stance="yes")
    b = Claim("y", ["H1", "H2"], 0.5, stance="yes")
    assert a.key() == b.key()


def test_explanation_claim_keys_and_by_evidence():
    exp = Explanation("yes", [
        Claim("a", ["E1"], 0.8, stance="yes"),
        Claim("b", ["E2"], 0.7, stance="yes"),
    ])
    assert len(exp.claim_keys()) == 2
    assert exp.claim_by_evidence()["E2"].text == "b"


def test_evidence_truncated_keeps_first_sentence():
    ev = Evidence("E1", "First sentence. Second sentence here.", "yes", 2.0)
    short = ev.truncated()
    assert short.text == "First sentence."
    assert short.supports == "yes" and short.weight == 2.0


def test_evidence_truncated_single_sentence_unchanged():
    ev = Evidence("E1", "Only one sentence.", "yes", 1.0)
    assert ev.truncated().text == "Only one sentence."


@pytest.mark.parametrize("paradox,min_claim,answer,expected", [
    (0.0, 0.9, 1.0, "stable"),
    (0.0, 0.5, 1.0, "fragile"),
    (0.2, 0.9, 1.0, "fragile"),
    (0.5, 0.9, 1.0, "unstable"),
    (0.0, 0.9, 0.4, "unstable"),
])
def test_verdict_for(paradox, min_claim, answer, expected):
    assert verdict_for(paradox, min_claim, answer) == expected


def test_perturbation_kinds_partitioned():
    all_kinds = set(PerturbationKind)
    assert SEMANTIC_PRESERVING_KINDS | EXPECTED_CHANGE_KINDS == all_kinds
    assert not (SEMANTIC_PRESERVING_KINDS & EXPECTED_CHANGE_KINDS)
    assert PerturbationKind.REPEAT_QUERY in SEMANTIC_PRESERVING_KINDS
    assert PerturbationKind.DROP_WEAK_EVIDENCE in EXPECTED_CHANGE_KINDS


def test_perturbation_labels():
    assert PerturbationKind.PARAPHRASE.label == "Paraphrase question"
    assert "control" in PerturbationKind.REPEAT_QUERY.label
