# Explanation Stability Audit — H-01 (order_sensitive)

Domain: health
Question: Should patient Aisha be escalated to urgent care?

## Baseline explanation

Answer: **escalate** (gold: escalate)

- H1 supports escalate: Temperature 39.2C. This is a high fever for (confidence 0.90)
- H2 supports escalate: Urgent care review: heart rate 124 bpm. Patient (confidence 0.90)

## Audit verdict: FRAGILE

- Answer stability: 1.000
- Explanation stability (mean claim Jaccard): 0.903
- Paradox rate (answer holds, explanation flips): 0.167
- Paradox rate, semantic-preserving perturbations only: 0.200
- Mean confidence drift: 0.000
- Main breaker: reorder_evidence

## Per-claim stability

- 0.92 — H1 supports escalate: Temperature 39.2C. This is a high fever for (broken by: reorder_evidence)
- 0.92 — H2 supports escalate: Urgent care review: heart rate 124 bpm. Patient (broken by: reorder_evidence)

## Per-perturbation paradox rate

- Repeat query (control): paradox 0.000, answer 1.000, explanation 1.000
- Paraphrase question: paradox 0.000, answer 1.000, explanation 1.000
- Synonym swap in evidence: paradox 0.000, answer 1.000, explanation 1.000
- Reorder evidence: paradox 0.667, answer 1.000, explanation 0.611
- Typo noise in question: paradox 0.000, answer 1.000, explanation 1.000
- Inject irrelevant passage: paradox 0.000, answer 1.000, explanation 1.000
- Drop weakest evidence: paradox 0.000, answer 1.000, explanation 1.000
- Truncate evidence text: paradox 0.000, answer 1.000, explanation 1.000

