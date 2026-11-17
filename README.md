# Explanation Stability Audit

Does an agent's explanation survive perturbations that leave its answer
unchanged? If the reasons flip while the answer holds, the explanation
is not the real reason — it is a story told after the fact. This tool
audits exactly that, claim by claim, and names the perturbation that
broke each claim.

## 1. The idea in 30 seconds

Give the audit a case (a question + evidence passages) and an explainer
agent. The audit perturbs the case eight ways — paraphrase the question,
swap synonyms, reorder the evidence, add typos, inject an irrelevant
passage, drop the weakest passage, truncate the evidence, or just ask
again — and re-runs the agent. For every perturbation it records
whether the answer held and whether the explanation held. The headline
metric is the **paradox rate**: the fraction of perturbations where the
answer stayed the same but the explanation changed.

```text
$ python -m explanation_stability_audit demo
Case H-01 [health]: Should patient Aisha be escalated to urgent care?
  stable           answer=escalate     paradox=0.000 verdict=stable
  order_sensitive  answer=escalate     paradox=0.167 verdict=fragile
  keyword_fragile  answer=escalate     paradox=0.417 verdict=fragile
  confident        answer=escalate     paradox=0.167 verdict=fragile
```

## 2. Quick start

```bash
pip install pytest streamlit   # streamlit is dashboard-only
python -m explanation_stability_audit demo
python -m explanation_stability_audit evaluate --out results
python -m explanation_stability_audit audit --case H-01 --agent order_sensitive
streamlit run app.py
```

Everything is offline, deterministic, and stdlib-only at runtime. No
model calls, no keys, no network. The four explainer agents are
scripted rule-based agents, so every number is reproducible from
`data/cases.json` (48 hand-designed cases across health triage, PHM
maintenance, and research QA).

## 3. Measured results

48 cases x 4 agents x 8 perturbations (12 runs per case-agent: reorder
and typo noise take 3 seeds each) = 192 audits.

| agent | paradox | paradox (semantic only) | answer stability | explanation stability | confidence drift | verdicts |
|---|---|---|---|---|---|---|
| stable | 0.003 | **0.000** | 1.000 | 0.999 | 0.000 | 48 stable |
| order_sensitive | 0.174 | 0.204 | 0.941 | 0.830 | 0.000 | 47 fragile, 1 stable |
| keyword_fragile | 0.165 | 0.133 | 0.898 | 0.814 | 0.053 | 37 fragile, 11 stable |
| confident | 0.167 | 0.100 | 1.000 | 0.969 | 0.000 | 48 fragile |

Headline paradox gap (most fragile minus stable, semantic only): **0.204**.

"Semantic only" means the six perturbations that must not change
anything: repeat, paraphrase, synonym swap, reorder, typo noise,
irrelevant injection. The other two — drop the weakest passage and
truncate the evidence — change the evidence itself, so a flip there is
honest sensitivity and is reported separately (expected-change paradox:
stable 0.021, order_sensitive 0.021, keyword_fragile 0.323, confident
0.500).

## 4. The paradox metric

An explanation is a set of claims; a claim is a (stance, cited
evidence) pair. The quoted words are illustration, not identity — a
synonym swap that rewords a quote without changing what it cites is
not a changed reason. Stability is the Jaccard similarity of the
claim set before and after a perturbation. A paradox is a run where
the answer is unchanged and the Jaccard is below 1.0.

Per-claim stability is the fraction of perturbations under which a
baseline claim survives, and every claim names its breaker — the
perturbation that broke it most often. The case verdict is `stable`
(no semantic paradox and every claim survives at least 80% of runs),
`fragile` (some semantic paradox, below 50%), or `unstable`.

## 5. Where each agent breaks

Per-perturbation paradox rate (semantic kinds only):

| perturbation | stable | order_sensitive | keyword_fragile | confident |
|---|---|---|---|---|
| Repeat query (control) | 0.000 | 0.000 | 0.000 | 0.000 |
| Paraphrase question | 0.000 | 0.000 | 0.292 | 0.000 |
| Synonym swap in evidence | 0.000 | 0.000 | 0.208 | 0.000 |
| Reorder evidence | 0.000 | **0.681** | 0.000 | 0.000 |
| Typo noise in question | 0.000 | 0.000 | 0.278 | 0.000 |
| Inject irrelevant passage | 0.000 | 0.000 | 0.000 | **1.000** |

Each fragile agent has exactly one signature: the order agent only
reads the first two passages, so reordering rewrites its reasons; the
keyword agent needs two shared keywords per passage, so paraphrase
(referent substitution: "patient Aisha" becomes "this person") and
synonym swaps strip its matches; the confident agent cites everything
at 0.95, so it cites the injected junk on every case — and its
confidence never moves (drift 0.000) even when its reasons change,
which is unresponsive, not stable.

## 6. Honest limits

- The agents are scripted, not LLMs: the audit measures explanation
  stability of *these* deterministic agents on synthetic cases, not of
  any production model. The numbers validate the auditor against its
  own contract; they are not real-world accuracy.
- Confidence drift is 0.000 for three agents because their confidence
  is a fixed property of the cited passage (or a fixed 0.95). Only the
  keyword agent's confidence moves, because it is tied to match
  quality. Drift is reported as-is; it is not a calibrated score.
- Truncate-evidence is a weak probe: with claim identity defined by
  (stance, evidence), cutting a passage's second sentence rarely
  changes a reason. Drop-weak-evidence is the real expected-change
  probe.
- The stable agent is stable by construction (it canonicalizes
  synonyms and sums weights over all passages). It is the control
  that proves the auditor can pass a good agent, not a discovery.
- Prior art: explanation-stability tooling exists at other levels —
  TrustXAI, xai-auditor, DASH, and AETHEL audit SHAP/LIME attribution
  vectors on tabular data; RobustExplain and LET measure LLM
  explanation consistency in one domain (recommendations) with live
  models; the Trajectory Instability paper measures action sequences,
  not explanations. Nothing found is an offline, deterministic,
  claim-level audit for agent explanations with per-claim attribution
  and the answer-holds-explanation-flips paradox metric. That gap is
  what this repo fills.

## 7. Layout

```text
explanation_stability_audit/   core package
  models.py                    cases, evidence, claims, audit results
  perturbations.py             the 8 deterministic perturbations
  explainers.py                the 4 scripted agents
  audit.py                     the audit engine + paradox metric
  evaluation.py                load cases, run the full audit
  report.py                    markdown reports + results writer
  cli.py                       demo / evaluate / audit / perturb
data/cases.json                48 cases (16 per domain)
notebooks/                     01 demo run, 02 evaluation experiment
examples/                      demo case, sample report, run_audit.py
scripts/build_cases.py         regenerates data/cases.json
scripts/reproduce_results.py   regenerates results/ + drift guard
results/                       evaluation.json/csv/summary.md, HEADLINE.md
app.py                         Streamlit dashboard (3 tabs)
tests/                         68 tests
```

Regenerate every number with `python scripts/reproduce_results.py` —
it fails if any headline number drifted from the committed
`results/evaluation.json` by more than 0.001.
