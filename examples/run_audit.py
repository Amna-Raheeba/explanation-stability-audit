"""Example: audit one case and print its report.

Run: ``python examples/run_audit.py`` (or pass --case P-02 --agent
order_sensitive). Prints the baseline explanation, the audit verdict,
the paradox rate, and the per-claim stability table.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from explanation_stability_audit.evaluation import load_cases  # noqa: E402
from explanation_stability_audit.report import case_report  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", default="H-01")
    parser.add_argument("--agent", default="order_sensitive")
    args = parser.parse_args()
    cases = {c.case_id: c for c in load_cases(ROOT / "data" / "cases.json")}
    print(case_report(cases[args.case], args.agent))


if __name__ == "__main__":
    main()
