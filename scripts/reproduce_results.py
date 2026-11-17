"""Regenerate results/ from data/cases.json and guard headline drift.

Run: ``python scripts/reproduce_results.py``. Rebuilds the case set
from scripts/build_cases.py, re-runs the full evaluation, writes
results/, and fails if any headline number drifted from the committed
results/evaluation.json by more than 0.001. That makes the numbers in
the README reproducible, not hand-typed.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from explanation_stability_audit.evaluation import evaluate, load_cases  # noqa: E402
from explanation_stability_audit.report import write_results  # noqa: E402

TOLERANCE = 0.001


def main() -> int:
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_cases

    build_cases.main()
    cases = load_cases(ROOT / "data" / "cases.json")
    audits, summaries, headline = evaluate(cases)
    committed_path = ROOT / "results" / "evaluation.json"
    old_headline = {}
    if committed_path.exists():
        old_headline = json.loads(
            committed_path.read_text(encoding="utf-8")).get("headline", {})
    write_results(ROOT / "results", audits, summaries, headline)
    drifted = []
    for key, old in old_headline.items():
        new = headline.get(key)
        if new is None or abs(new - old) > TOLERANCE:
            drifted.append((key, old, new))
    print("Regenerated %d audits; headline numbers:" % len(audits))
    for key in sorted(headline):
        print("  %-38s %.4f" % (key, headline[key]))
    if drifted:
        for key, old, new in drifted:
            print("DRIFT: %s was %.4f, now %.4f" % (key, old, new))
        return 1
    print("No headline drift (tolerance %.3f)." % TOLERANCE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
