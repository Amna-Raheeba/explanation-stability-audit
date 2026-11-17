"""Tests for markdown reports and results writing."""

import json

from explanation_stability_audit.evaluation import evaluate, load_cases
from explanation_stability_audit.report import (
    case_report,
    summary_markdown,
    write_results,
)


def test_case_report_contains_verdict_and_numbers():
    cases = load_cases("data/cases.json")
    text = case_report(cases[0], "order_sensitive")
    assert "order_sensitive" in text
    assert "Audit verdict" in text
    assert "Paradox rate" in text
    assert "Per-claim stability" in text
    assert "Per-perturbation paradox rate" in text


def test_summary_markdown_lists_all_agents():
    cases = load_cases("data/cases.json")
    audits, summaries, _headline = evaluate(cases)
    text = summary_markdown(summaries, audits)
    for agent in ("stable", "order_sensitive", "keyword_fragile",
                  "confident"):
        assert agent in text


def test_write_results_writes_four_files(tmp_path):
    cases = load_cases("data/cases.json")
    audits, summaries, headline = evaluate(cases)
    write_results(tmp_path, audits, summaries, headline)
    names = {p.name for p in tmp_path.iterdir()}
    assert names == {"evaluation.json", "evaluation.csv",
                     "evaluation_summary.md", "HEADLINE.md"}
    data = json.loads((tmp_path / "evaluation.json").read_text())
    assert len(data["rows"]) == 192
    assert data["headline"]["paradox_gap"] > 0.15
    csv_lines = (tmp_path / "evaluation.csv").read_text().splitlines()
    assert len(csv_lines) == 193  # header + 192 rows
    assert "Paradox rate" in (tmp_path / "HEADLINE.md").read_text()
