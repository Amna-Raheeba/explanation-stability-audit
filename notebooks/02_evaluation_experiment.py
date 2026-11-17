"""Notebook 02 — evaluation experiment: the full 48-case audit.

Runnable as a plain script: ``python notebooks/02_evaluation_experiment.py``.
Reproduces the numbers in results/: per-agent paradox rates, the
semantic-only paradox rates, the per-kind breaker table, and the
headline paradox gap between the stable agent and the most fragile
one. Every number is recomputed from data/cases.json; nothing is
hard-coded.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from explanation_stability_audit.evaluation import evaluate, load_cases  # noqa: E402
from explanation_stability_audit.models import PerturbationKind  # noqa: E402


def main() -> None:
    cases = load_cases(ROOT / "data" / "cases.json")
    audits, summaries, headline = evaluate(cases)
    print("Cases: %d, audits: %d" % (len(cases), len(audits)))
    print()
    print("%-16s %8s %8s %8s %8s %8s" % (
        "agent", "paradox", "sem.", "answer", "expl.", "drift"))
    for agent, s in summaries.items():
        print("%-16s %8.3f %8.3f %8.3f %8.3f %8.3f  %s" % (
            agent, s.mean_paradox_rate, s.mean_paradox_rate_semantic,
            s.mean_answer_stability, s.mean_explanation_stability,
            s.mean_confidence_drift,
            dict(sorted(s.verdict_counts.items()))))
    print()
    print("Per-kind paradox rate (semantic kinds only):")
    print("%-28s %8s %8s %8s %8s" % (
        "perturbation", "stable", "order", "keyword", "confid."))
    for kind in PerturbationKind:
        if kind.value in ("drop_weak_evidence", "truncate_evidence"):
            continue
        print("%-28s %8.3f %8.3f %8.3f %8.3f" % (
            kind.label,
            summaries["stable"].per_kind_paradox[kind.value],
            summaries["order_sensitive"].per_kind_paradox[kind.value],
            summaries["keyword_fragile"].per_kind_paradox[kind.value],
            summaries["confident"].per_kind_paradox[kind.value]))
    print()
    print("Headline paradox gap (most fragile minus stable): %.3f"
          % headline["paradox_gap"])
    print("Expected-change paradox (evidence itself changed, honest "
          "sensitivity, not instability):")
    for agent in summaries:
        print("  %-16s %.3f" % (
            agent, headline["%s_expected_change_paradox" % agent]))


if __name__ == "__main__":
    main()
