"""Tests for evaluation loading and headline numbers."""

from explanation_stability_audit.evaluation import evaluate, load_cases


def test_load_cases_count_and_domains():
    cases = load_cases("data/cases.json")
    assert len(cases) == 48
    domains = {c.domain for c in cases}
    assert domains == {"health", "phm", "research"}
    assert all(len(c.evidence) == 5 for c in cases)
    assert all(c.gold_claims for c in cases)


def test_load_cases_gold_answers_cover_all_labels():
    cases = load_cases("data/cases.json")
    health = {c.gold_answer for c in cases if c.domain == "health"}
    phm = {c.gold_answer for c in cases if c.domain == "phm"}
    research = {c.gold_answer for c in cases if c.domain == "research"}
    assert health == {"escalate", "monitor", "routine"}
    assert phm == {"offline_now", "schedule", "keep_running"}
    assert research == {"yes", "no", "inconclusive"}


def test_evaluate_counts():
    cases = load_cases("data/cases.json")
    audits, summaries, headline = evaluate(cases)
    assert len(audits) == 192
    assert set(summaries) == {
        "stable", "order_sensitive", "keyword_fragile", "confident"}
    assert headline["n_cases"] == 48.0
    assert headline["n_audits"] == 192.0


def test_evaluate_headline_separates_agents():
    cases = load_cases("data/cases.json")
    _audits, summaries, headline = evaluate(cases)
    stable = summaries["stable"]
    assert stable.mean_paradox_rate_semantic == 0.0
    assert stable.mean_answer_stability == 1.0
    fragile = max(summaries.values(),
                  key=lambda s: s.mean_paradox_rate_semantic)
    assert fragile.agent == "order_sensitive"
    assert headline["paradox_gap"] > 0.15


def test_evaluate_expected_change_reported_separately():
    cases = load_cases("data/cases.json")
    _audits, _summaries, headline = evaluate(cases)
    # The confident agent flips on every expected-change run (it cites
    # whatever it is given), but that is honest sensitivity, not a
    # semantic paradox: its semantic rate stays low.
    assert headline["confident_expected_change_paradox"] > 0.4
    assert headline["confident_paradox_rate_semantic"] < 0.2
