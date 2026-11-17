"""Tests for perturbations: determinism, effect, and invariants."""

import pytest

from explanation_stability_audit.evaluation import load_cases
from explanation_stability_audit.models import Case, Evidence, PerturbationKind
from explanation_stability_audit.perturbations import (
    IRRELEVANT,
    apply_perturbation,
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
        ],
        "escalate",
    )


def test_repeat_query_is_identity():
    case = _case()
    out = apply_perturbation(case, PerturbationKind.REPEAT_QUERY, 1)
    assert out.question == case.question
    assert out.evidence == case.evidence
    assert out.gold_answer == case.gold_answer


def test_perturbations_are_deterministic():
    case = _case()
    for kind in PerturbationKind:
        a = apply_perturbation(case, kind, 1)
        b = apply_perturbation(case, kind, 1)
        assert a == b, kind


def test_reorder_changes_order_but_not_content():
    case = _case()
    orders = [
        tuple(e.id for e in apply_perturbation(
            case, PerturbationKind.REORDER_EVIDENCE, s).evidence)
        for s in (1, 2, 3, 4, 5)
    ]
    assert any(o != ("H1", "H2", "H3") for o in orders)
    for order in orders:
        assert sorted(order) == ["H1", "H2", "H3"]


def test_reorder_differs_across_seeds():
    case = _case()
    orders = {
        tuple(e.id for e in apply_perturbation(
            case, PerturbationKind.REORDER_EVIDENCE, s).evidence)
        for s in (1, 2, 3)
    }
    assert len(orders) > 1


def test_paraphrase_substitutes_referent_and_synonyms():
    case = _case()
    out = apply_perturbation(case, PerturbationKind.PARAPHRASE, 1)
    assert "Aisha" not in out.question
    # "patient Aisha" -> "this patient" -> "this person" (synonym map).
    assert "this person" in out.question
    assert "urgent" not in out.question  # urgent -> immediate
    assert "care" in out.question


def test_synonym_swap_changes_mapped_words_only():
    case = _case()
    out = apply_perturbation(case, PerturbationKind.SYNONYM_SWAP, 1)
    joined = " ".join(e.text for e in out.evidence)
    assert "danger" in joined or "person" in joined
    assert "risk" not in joined  # risk -> danger
    assert [e.id for e in out.evidence] == ["H1", "H2", "H3"]
    assert [e.supports for e in out.evidence] == [
        e.supports for e in case.evidence]


def test_typo_noise_changes_question_not_evidence():
    case = _case()
    out = apply_perturbation(case, PerturbationKind.TYPO_NOISE, 1)
    assert out.question != case.question
    assert out.evidence == case.evidence


def test_irrelevant_injection_appends_zero_weight_passage():
    case = _case()
    out = apply_perturbation(case, PerturbationKind.IRRELEVANT_INJECTION, 1)
    assert len(out.evidence) == 4
    extra = out.evidence[-1]
    assert extra.id == "X1" and extra.weight == 0.0
    assert extra.supports == "none"


def test_irrelevant_pool_covers_all_domains():
    assert set(IRRELEVANT) == {"health", "phm", "research"}


def test_drop_weak_removes_lowest_weight():
    case = _case()
    out = apply_perturbation(case, PerturbationKind.DROP_WEAK_EVIDENCE, 1)
    assert [e.id for e in out.evidence] == ["H1", "H2"]


def test_truncate_shortens_every_passage():
    case = _case()
    out = apply_perturbation(case, PerturbationKind.TRUNCATE_EVIDENCE, 1)
    for before, after in zip(case.evidence, out.evidence):
        assert len(after.text) <= len(before.text)
        assert after.text.endswith(".")
    assert any(a.text != b.text
               for a, b in zip(out.evidence, case.evidence))


def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        apply_perturbation(_case(), "not_a_kind", 1)  # type: ignore[arg-type]


def test_every_perturbation_changes_something_somewhere():
    """Each kind must actually perturb at least one of the 48 cases."""
    cases = load_cases("data/cases.json")
    for kind in PerturbationKind:
        changed = any(
            apply_perturbation(c, kind, 1) != c for c in cases)
        assert changed, kind
