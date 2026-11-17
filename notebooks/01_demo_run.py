"""Notebook 01 — demo run: audit one case under all four agents.

Runnable as a plain script: ``python notebooks/01_demo_run.py``.
Shows the baseline explanation of each agent for case H-01, then the
paradox rate each agent earns on it, and which perturbation broke
which claim.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from explanation_stability_audit.audit import audit_case  # noqa: E402
from explanation_stability_audit.evaluation import load_cases  # noqa: E402
from explanation_stability_audit.explainers import AGENTS, explain  # noqa: E402
from explanation_stability_audit.models import PerturbationKind  # noqa: E402


def main() -> None:
    cases = load_cases(ROOT / "data" / "cases.json")
    case = next(c for c in cases if c.case_id == "H-01")
    print("Case %s [%s]" % (case.case_id, case.domain))
    print("Q: %s" % case.question)
    print("Gold answer: %s" % case.gold_answer)
    for agent in AGENTS:
        explanation = explain(case, agent)
        audit = audit_case(case, agent)
        print("\n--- %s: answer=%s paradox=%.3f (semantic %.3f) "
              "verdict=%s" % (agent, explanation.answer, audit.paradox_rate,
                              audit.paradox_rate_semantic, audit.verdict))
        for claim in explanation.claims:
            print("  - %s (%.2f)" % (claim.text, claim.confidence))
        for kind in PerturbationKind:
            row = audit.per_kind[kind.value]
            if row["paradox_rate"] > 0:
                print("  ! %s: paradox %.3f" % (kind.label, row["paradox_rate"]))
        for cs in audit.claim_stability:
            if cs.survival_rate < 1.0:
                print("  claim %.2f survived, broken by %s: %s"
                      % (cs.survival_rate, cs.breaker, cs.claim_text))


if __name__ == "__main__":
    main()
