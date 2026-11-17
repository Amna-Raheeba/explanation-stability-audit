"""Markdown reports: per-case audit reports and the evaluation summary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Sequence

from .audit import audit_case
from .explainers import explain
from .models import AgentSummary, Case, CaseAudit, PerturbationKind


def case_report(case: Case, agent: str) -> str:
    """A human-readable audit report for one case under one agent."""
    audit = audit_case(case, agent)
    baseline = explain(case, agent)
    lines = [
        "# Explanation Stability Audit — %s (%s)" % (case.case_id, agent),
        "",
        "Domain: %s" % case.domain,
        "Question: %s" % case.question,
        "",
        "## Baseline explanation",
        "",
        "Answer: **%s** (gold: %s)" % (baseline.answer, case.gold_answer),
        "",
    ]
    for claim in baseline.claims:
        lines.append("- %s (confidence %.2f)" % (claim.text, claim.confidence))
    lines += [
        "",
        "## Audit verdict: %s" % audit.verdict.upper(),
        "",
        "- Answer stability: %.3f" % audit.answer_stability,
        "- Explanation stability (mean claim Jaccard): %.3f"
        % audit.explanation_stability,
        "- Paradox rate (answer holds, explanation flips): %.3f"
        % audit.paradox_rate,
        "- Paradox rate, semantic-preserving perturbations only: %.3f"
        % audit.paradox_rate_semantic,
        "- Mean confidence drift: %.3f" % audit.mean_confidence_drift,
        "- Main breaker: %s" % (audit.breaker or "none"),
        "",
        "## Per-claim stability",
        "",
    ]
    for cs in audit.claim_stability:
        lines.append(
            "- %.2f — %s (broken by: %s)"
            % (cs.survival_rate, cs.claim_text, cs.breaker or "nothing")
        )
    lines += ["", "## Per-perturbation paradox rate", ""]
    for kind in PerturbationKind:
        row = audit.per_kind[kind.value]
        lines.append("- %s: paradox %.3f, answer %.3f, explanation %.3f"
                     % (kind.label, row["paradox_rate"],
                        row["answer_stability"], row["explanation_stability"]))
    lines.append("")
    return "\n".join(lines)


def summary_markdown(summaries: Dict[str, AgentSummary],
                     audits: Sequence[CaseAudit]) -> str:
    """The evaluation summary: one section per agent, then the gap."""
    lines = [
        "# Explanation Stability Audit — Evaluation Summary",
        "",
        "Cases: %d, agents: %d, audits: %d"
        % (len({a.case_id for a in audits}), len(summaries), len(audits)),
        "",
        "The paradox rate is the fraction of perturbations where the "
        "answer stayed the same but the explanation changed. A "
        "trustworthy explanation must not flip while its answer holds.",
        "",
    ]
    for agent, s in summaries.items():
        lines += [
            "## %s" % agent,
            "",
            "- Mean paradox rate: %.3f" % s.mean_paradox_rate,
            "- Mean paradox rate (semantic-preserving only): %.3f"
            % s.mean_paradox_rate_semantic,
            "- Mean answer stability: %.3f" % s.mean_answer_stability,
            "- Mean explanation stability: %.3f" % s.mean_explanation_stability,
            "- Mean confidence drift: %.3f" % s.mean_confidence_drift,
            "- Verdicts: %s"
            % ", ".join("%s %d" % (k, v)
                        for k, v in sorted(s.verdict_counts.items())),
            "- Worst cases: %s" % ", ".join(s.worst_cases),
            "",
            "Per-perturbation paradox rate:",
            "",
        ]
        for kind in PerturbationKind:
            lines.append("- %s: %.3f"
                         % (kind.label, s.per_kind_paradox[kind.value]))
        lines.append("")
    return "\n".join(lines)


def write_results(out_dir: str | Path, audits: Sequence[CaseAudit],
                  summaries: Dict[str, AgentSummary],
                  headline: Dict[str, float]) -> None:
    """Write evaluation.json, evaluation.csv, summary.md, HEADLINE.md."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for a in audits:
        rows.append({
            "case_id": a.case_id,
            "domain": a.domain,
            "agent": a.agent,
            "verdict": a.verdict,
            "answer_stability": round(a.answer_stability, 4),
            "explanation_stability": round(a.explanation_stability, 4),
            "paradox_rate": round(a.paradox_rate, 4),
            "paradox_rate_semantic": round(a.paradox_rate_semantic, 4),
            "confidence_drift": round(a.mean_confidence_drift, 4),
            "min_claim_stability": round(a.min_claim_stability, 4),
            "breaker": a.breaker,
        })
    (out / "evaluation.json").write_text(
        json.dumps({"headline": {k: round(v, 4) for k, v in headline.items()},
                    "rows": rows}, indent=2), encoding="utf-8")
    header = list(rows[0].keys()) if rows else []
    csv_lines = [",".join(header)]
    for r in rows:
        csv_lines.append(",".join(
            "" if r[h] is None else str(r[h]) for h in header))
    (out / "evaluation.csv").write_text("\n".join(csv_lines) + "\n",
                                         encoding="utf-8")
    (out / "evaluation_summary.md").write_text(
        summary_markdown(summaries, audits), encoding="utf-8")
    stable = summaries.get("stable")
    fragile = max(summaries.values(),
                  key=lambda s: s.mean_paradox_rate_semantic)
    (out / "HEADLINE.md").write_text(
        "# Headline\n\n"
        "Paradox rate (semantic-preserving perturbations): "
        "stable agent %.3f, %s agent %.3f, gap %.3f.\n\n"
        "Mean explanation stability: stable %.3f, %s %.3f.\n"
        % (stable.mean_paradox_rate_semantic if stable else 0.0,
           fragile.agent, fragile.mean_paradox_rate_semantic,
           headline.get("paradox_gap", 0.0),
           stable.mean_explanation_stability if stable else 0.0,
           fragile.agent, fragile.mean_explanation_stability),
        encoding="utf-8")
