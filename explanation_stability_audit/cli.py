"""Command line: demo, evaluate, audit one case."""

from __future__ import annotations

import argparse
import sys

from .audit import audit_case
from .evaluation import default_cases_path, evaluate, load_cases
from .explainers import AGENTS, explain
from .models import PerturbationKind
from .perturbations import apply_perturbation
from .report import case_report, write_results


def _cmd_demo(_args: argparse.Namespace) -> int:
    cases = load_cases(default_cases_path())
    case = cases[0]
    print("Case %s [%s]: %s" % (case.case_id, case.domain, case.question))
    for agent in AGENTS:
        explanation = explain(case, agent)
        audit = audit_case(case, agent)
        print("  %-16s answer=%-12s paradox=%.3f verdict=%s"
              % (agent, explanation.answer, audit.paradox_rate,
                 audit.verdict))
    print("Run `python -m explanation_stability_audit evaluate` "
          "for the full %d-case audit." % len(cases))
    return 0


def _cmd_evaluate(args: argparse.Namespace) -> int:
    cases = load_cases(default_cases_path())
    audits, summaries, headline = evaluate(cases)
    write_results(args.out, audits, summaries, headline)
    for agent, s in summaries.items():
        print("%-16s paradox=%.3f (semantic %.3f) answer=%.3f "
              "explanation=%.3f verdicts=%s"
              % (agent, s.mean_paradox_rate, s.mean_paradox_rate_semantic,
                 s.mean_answer_stability, s.mean_explanation_stability,
                 dict(sorted(s.verdict_counts.items()))))
    print("Wrote %d audits to %s" % (len(audits), args.out))
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    cases = {c.case_id: c for c in load_cases(default_cases_path())}
    if args.case not in cases:
        print("unknown case: %s (try one of %s)"
              % (args.case, ", ".join(sorted(cases)[:5])), file=sys.stderr)
        return 2
    print(case_report(cases[args.case], args.agent))
    return 0


def _cmd_perturb(args: argparse.Namespace) -> int:
    cases = {c.case_id: c for c in load_cases(default_cases_path())}
    if args.case not in cases:
        print("unknown case: %s" % args.case, file=sys.stderr)
        return 2
    kind = PerturbationKind(args.kind)
    perturbed = apply_perturbation(cases[args.case], kind, args.seed)
    print("Original: %s" % cases[args.case].question)
    print("Perturbed (%s): %s" % (kind.label, perturbed.question))
    for ev in perturbed.evidence:
        print("  %s [%s w=%.1f]: %s" % (ev.id, ev.supports, ev.weight, ev.text))
    return 0


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="explanation-stability-audit")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="audit the first case under all agents")
    p_eval = sub.add_parser("evaluate", help="run the full audit")
    p_eval.add_argument("--out", default="results")
    p_audit = sub.add_parser("audit", help="audit one case under one agent")
    p_audit.add_argument("--case", required=True)
    p_audit.add_argument("--agent", default="stable", choices=list(AGENTS))
    p_pert = sub.add_parser("perturb", help="show one perturbation")
    p_pert.add_argument("--case", required=True)
    p_pert.add_argument("--kind", required=True,
                        choices=[k.value for k in PerturbationKind])
    p_pert.add_argument("--seed", type=int, default=1)
    args = parser.parse_args(argv)
    if args.command == "demo":
        return _cmd_demo(args)
    if args.command == "evaluate":
        return _cmd_evaluate(args)
    if args.command == "audit":
        return _cmd_audit(args)
    if args.command == "perturb":
        return _cmd_perturb(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
