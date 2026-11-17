# Changelog

## 0.1.0 — 2026-11-17

- First release: Explanation Stability Audit.
- 48 hand-designed cases (16 each: health triage, PHM maintenance,
  research QA) with gold answers asserted against the weight argmax.
- 8 deterministic perturbations: repeat (control), paraphrase with
  referent substitution, synonym swap, evidence reorder, typo noise,
  irrelevant injection, drop weakest evidence, truncate evidence.
- 4 scripted explainer agents: stable (canonicalizing, order- and
  injection-invariant), order-sensitive (primacy bias), keyword-fragile
  (two-keyword exact match, confidence tied to match quality),
  confident (cites everything at 0.95).
- Headline metric: paradox rate — answer holds while the explanation
  flips. Semantic-only paradox: stable 0.000, order-sensitive 0.204,
  keyword-fragile 0.133, confident 0.100. Gap 0.204.
- Per-claim stability with breaker attribution (rates, not counts, so
  three-seed kinds are not weighted 3x); expected-change kinds
  (drop/truncate) reported separately and excluded from verdicts and
  breakers.
- Streamlit dashboard (Case Explorer, Paradox Analysis, Evaluation),
  two runnable notebooks, CLI (demo / evaluate / audit / perturb),
  reproduce script with headline-drift guard.
- 68 tests, all passing on Python 3.12; CI matrix 3.10/3.11/3.12.
