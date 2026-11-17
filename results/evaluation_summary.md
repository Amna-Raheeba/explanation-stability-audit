# Explanation Stability Audit — Evaluation Summary

Cases: 48, agents: 4, audits: 192

The paradox rate is the fraction of perturbations where the answer stayed the same but the explanation changed. A trustworthy explanation must not flip while its answer holds.

## stable

- Mean paradox rate: 0.003
- Mean paradox rate (semantic-preserving only): 0.000
- Mean answer stability: 1.000
- Mean explanation stability: 0.999
- Mean confidence drift: 0.000
- Verdicts: stable 48
- Worst cases: H-03, H-11, H-01, H-02, H-04

Per-perturbation paradox rate:

- Repeat query (control): 0.000
- Paraphrase question: 0.000
- Synonym swap in evidence: 0.000
- Reorder evidence: 0.000
- Typo noise in question: 0.000
- Inject irrelevant passage: 0.000
- Drop weakest evidence: 0.042
- Truncate evidence text: 0.000

## order_sensitive

- Mean paradox rate: 0.174
- Mean paradox rate (semantic-preserving only): 0.204
- Mean answer stability: 0.941
- Mean explanation stability: 0.830
- Mean confidence drift: 0.000
- Verdicts: fragile 47, stable 1
- Worst cases: H-02, H-03, H-05, H-06, H-07

Per-perturbation paradox rate:

- Repeat query (control): 0.000
- Paraphrase question: 0.000
- Synonym swap in evidence: 0.000
- Reorder evidence: 0.681
- Typo noise in question: 0.000
- Inject irrelevant passage: 0.000
- Drop weakest evidence: 0.042
- Truncate evidence text: 0.000

## keyword_fragile

- Mean paradox rate: 0.165
- Mean paradox rate (semantic-preserving only): 0.133
- Mean answer stability: 0.898
- Mean explanation stability: 0.814
- Mean confidence drift: 0.053
- Verdicts: fragile 37, stable 11
- Worst cases: H-01, H-16, R-07, H-02, H-07

Per-perturbation paradox rate:

- Repeat query (control): 0.000
- Paraphrase question: 0.292
- Synonym swap in evidence: 0.208
- Reorder evidence: 0.000
- Typo noise in question: 0.278
- Inject irrelevant passage: 0.000
- Drop weakest evidence: 0.042
- Truncate evidence text: 0.604

## confident

- Mean paradox rate: 0.167
- Mean paradox rate (semantic-preserving only): 0.100
- Mean answer stability: 1.000
- Mean explanation stability: 0.969
- Mean confidence drift: 0.000
- Verdicts: fragile 48
- Worst cases: H-01, H-02, H-03, H-04, H-05

Per-perturbation paradox rate:

- Repeat query (control): 0.000
- Paraphrase question: 0.000
- Synonym swap in evidence: 0.000
- Reorder evidence: 0.000
- Typo noise in question: 0.000
- Inject irrelevant passage: 1.000
- Drop weakest evidence: 1.000
- Truncate evidence text: 0.000
