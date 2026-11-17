"""Build data/cases.json: 48 hand-designed cases, 16 per domain.

Each domain has 8 templates; each template is instantiated twice
with different surface values (names, numbers, ids) that stay in the
same semantic band, so the gold answer never changes. Every evidence
passage has two sentences: a short first sentence (the key fact) and
a second sentence with detail, so the truncate_evidence perturbation
actually changes what an agent can quote. Every passage also shares
at least one keyword with its question, so the keyword-matching agent
has something to match.

Gold answers are asserted against the weight argmax, and gold claims
are the stable agent's own explanation of the unperturbed case.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from explanation_stability_audit.explainers import explain_stable  # noqa: E402
from explanation_stability_audit.models import Case, Evidence  # noqa: E402

# (question, [(text, supports, weight, strength)], gold_answer)
# Supports labels are per-domain answer labels.
HEALTH = [
    ("Should patient {name} be escalated to urgent care?",
     [("Temperature 39.2C. This is a high fever for patient {name}, "
       "and the risk is severe.", "escalate", 2.0, 0.9),
      ("Urgent care review: heart rate 124 bpm. Patient {name} has a "
       "high heart rate, and the risk is severe.", "escalate", 2.0, 0.9),
      ("Patient {name} reports a severe headache. The headache is "
       "severe and the patient should be checked.", "escalate", 1.0, 0.8),
      ("Patient {name} has a history of asthma. Asthma should be "
       "monitored, so the patient needs watching.", "monitor", 1.0, 0.7),
      ("Patient {name} feels slightly better today. The fever is high "
       "but the patient feels better.", "routine", 0.5, 0.6)],
     "escalate"),
    ("Should patient {name} be escalated to urgent care?",
     [("Patient {name} reports chest pain. The pain is severe and the "
       "patient should be checked at once.", "escalate", 2.0, 0.9),
      ("Urgent care review: oxygen saturation 91 percent. Patient "
       "{name} has low oxygen, and the risk is high.", "escalate", 2.0, 0.9),
      ("Patient {name} had an ECG. The ECG is normal, so the patient "
       "should be monitored.", "monitor", 1.0, 0.8),
      ("Patient {name} is 68 years old. Older patients carry a high "
       "risk and should be checked.", "escalate", 1.0, 0.7),
      ("Patient {name} has no fever. The patient feels calm and the "
       "temperature is low.", "routine", 0.5, 0.6)],
     "escalate"),
    ("Should patient {name} be escalated to urgent care?",
     [("Patient {name} has a mild cough. The cough started 2 days ago "
       "and the patient feels well.", "routine", 1.5, 0.8),
      ("Temperature 37.1C. The temperature is low and normal for "
       "patient {name}.", "routine", 1.5, 0.9),
      ("Heart rate 78 bpm. The heart rate is normal, so patient "
       "{name} can be watched at home.", "routine", 1.0, 0.8),
      ("Patient {name} has no chronic illness. The patient should be "
       "checked again only if symptoms increase.", "routine", 1.0, 0.7),
      ("Patient {name} has a mild sore throat. The throat should be "
       "monitored for a few days.", "monitor", 1.0, 0.7)],
     "routine"),
    ("Should patient {name} be escalated to urgent care?",
     [("Patient {name} has redness around the wound. The redness is "
       "spreading, so the wound should be monitored.", "monitor", 2.0, 0.9),
      ("Temperature 38.1C. The temperature is high for patient {name}, "
       "so the patient should be watched.", "monitor", 1.5, 0.8),
      ("Patient {name} reports moderate pain. The pain should be "
       "monitored and the patient checked again.", "monitor", 1.0, 0.8),
      ("The nurse found the wound clean. Patient {name} has a clean "
       "wound, so routine care is enough.", "routine", 1.0, 0.7),
      ("Patient {name} has no discharge. There is no discharge, so "
       "the risk is low.", "routine", 0.5, 0.6)],
     "monitor"),
    ("Should patient {name} be escalated to urgent care?",
     [("Blood glucose 320 mg/dL. Patient {name} has a high glucose "
       "level, and the risk is severe.", "escalate", 2.0, 0.9),
      ("Urgent care review: ketones are present. Patient {name} has "
       "ketones, so the patient should be checked at once.",
       "escalate", 2.0, 0.9),
      ("Patient {name} feels nauseous. The nausea is severe and the "
       "patient should be examined.", "escalate", 1.0, 0.8),
      ("Patient {name} took insulin. The insulin should be monitored, "
       "so the patient needs watching.", "monitor", 1.0, 0.7),
      ("Patient {name} is alert and talking. The patient is alert, so "
       "the risk is lower.", "routine", 0.5, 0.6)],
     "escalate"),
    ("Should patient {name} be escalated to urgent care?",
     [("Temperature 38.5C. Patient {name} has a high fever, so the "
       "patient should be monitored.", "monitor", 2.0, 0.9),
      ("Patient {name} has ear pain. The ear pain is severe and the "
       "patient should be checked.", "monitor", 1.5, 0.8),
      ("Patient {name} is drinking fluids. The patient drinks well, "
       "so routine care is enough.", "routine", 1.0, 0.8),
      ("Patient {name} has no rash. There is no rash, so the risk is "
       "low for the patient.", "routine", 1.0, 0.7),
      ("Patient {name} slept restlessly. The sleep was restless, so "
       "the patient should be monitored.", "monitor", 1.0, 0.7)],
     "monitor"),
    ("Should patient {name} be escalated to urgent care?",
     [("Patient {name} fell from a chair. The fall was low risk and "
       "the patient should be checked once.", "routine", 1.5, 0.8),
      ("No head strike occurred. Patient {name} has no head injury, "
       "so the risk is low.", "routine", 1.5, 0.9),
      ("Patient {name} is alert. The patient is alert and talking, so "
       "routine care is enough.", "routine", 1.0, 0.8),
      ("Patient {name} has a bruise on the knee. The bruise should be "
       "monitored for a few days.", "monitor", 1.0, 0.7),
      ("Patient {name} walks with help. The patient should be watched "
       "while walking.", "monitor", 0.5, 0.6)],
     "routine"),
    ("Should patient {name} be escalated to urgent care?",
     [("Wheeze is audible. Patient {name} has a severe wheeze, so the "
       "patient should be checked at once.", "escalate", 2.0, 0.9),
      ("Urgent care review: oxygen saturation 93 percent. Patient "
       "{name} has low oxygen, and the risk is high.", "escalate", 1.5, 0.9),
      ("The inhaler is not helping. Patient {name} used the inhaler, "
       "but the wheeze is still severe.", "escalate", 1.5, 0.8),
      ("Patient {name} has a history of COPD. COPD carries a high "
       "risk and should be monitored.", "escalate", 1.0, 0.7),
      ("Patient {name} speaks in full sentences. The patient speaks "
       "well, so the risk is lower.", "monitor", 1.0, 0.6)],
     "escalate"),
]

PHM = [
    ("Should {asset} be taken offline now for maintenance?",
     [("{asset} vibration increased 40 percent. The vibration is high "
       "and the shaking should be checked.", "schedule", 2.0, 0.9),
      ("{asset} temperature is normal. The heat is low, so the asset "
       "can keep running.", "keep_running", 1.0, 0.8),
      ("Remaining life estimate 320 hours. The estimate is high, so "
       "{asset} maintenance can be scheduled.", "schedule", 1.5, 0.8),
      ("Last inspection of {asset} was clean. The inspection found no "
       "cause for urgent maintenance.", "keep_running", 1.0, 0.7),
      ("Noise was reported from {asset}. The noise should be monitored "
       "and the vibration checked.", "schedule", 1.0, 0.7)],
     "schedule"),
    ("Should {asset} be taken offline now for maintenance?",
     [("Bearing temperature 95C. The heat is high for {asset}, and the "
       "risk of failure is severe.", "offline_now", 2.0, 0.9),
      ("Vibration is severe. The shaking is severe for {asset}, so "
       "maintenance should happen now.", "offline_now", 2.0, 0.9),
      ("Leakage is visible on {asset}. The leak should be checked and "
       "the asset taken offline.", "offline_now", 1.5, 0.8),
      ("A spare for {asset} is available. The spare makes scheduled "
       "maintenance possible.", "schedule", 1.0, 0.7),
      ("Production has a deadline. The deadline means {asset} should "
       "keep running if possible.", "keep_running", 0.5, 0.6)],
     "offline_now"),
    ("Should {asset} be taken offline now for maintenance?",
     [("Belt wear is within limits. The wear is low for {asset}, so "
       "maintenance is not urgent.", "keep_running", 2.0, 0.9),
      ("Motor current is normal. The current is low and normal, so "
       "{asset} can keep running.", "keep_running", 1.5, 0.8),
      ("No noise from {asset}. The asset is quiet, so the risk is "
       "low.", "keep_running", 1.0, 0.8),
      ("Next service for {asset} is in 2 weeks. The service should be "
       "scheduled as planned.", "schedule", 1.0, 0.7),
      ("Minor dust on {asset}. The dust should be monitored but does "
       "not cause failure.", "schedule", 0.5, 0.6)],
     "keep_running"),
    ("Should {asset} be taken offline now for maintenance?",
     [("Pressure dropped 12 percent. The pressure is low for {asset}, "
       "so maintenance should be scheduled.", "schedule", 2.0, 0.9),
      ("The filter is clogged. A clogged filter can cause a pressure "
       "drop, so {asset} should be checked.", "schedule", 1.5, 0.8),
      ("Temperature is slightly high. The heat is slightly high for "
       "{asset}, so it should be monitored.", "schedule", 1.0, 0.7),
      ("Output is still in spec. {asset} output is normal, so it can "
       "keep running.", "keep_running", 1.0, 0.8),
      ("No leaks on {asset}. There is no leak, so the risk is low.",
       "keep_running", 0.5, 0.6)],
     "schedule"),
    ("Should {asset} be taken offline now for maintenance?",
     [("Insulation resistance 0.4 MOhm. The resistance is low for "
       "{asset}, and the risk of failure is severe.", "offline_now",
       2.0, 0.9),
      ("{asset} tripped twice. The trips show a severe fault, so "
       "maintenance should happen now.", "offline_now", 2.0, 0.9),
      ("Burning smell from {asset}. The smell is a severe warning, so "
       "the asset should be checked at once.", "offline_now", 1.5, 0.8),
      ("Load on {asset} is light. A light load means scheduled "
       "maintenance is possible.", "schedule", 1.0, 0.7),
      ("Backup motor is ready. The backup means {asset} can be taken "
       "offline for maintenance.", "schedule", 0.5, 0.6)],
     "offline_now"),
    ("Should {asset} be taken offline now for maintenance?",
     [("Iron particles are rising in the oil. The particles show wear "
       "in {asset}, so maintenance should be scheduled.", "schedule",
       2.0, 0.9),
      ("Oil is dark. Dark oil can cause wear, so {asset} should be "
       "checked soon.", "schedule", 1.5, 0.8),
      ("Vibration is normal. The shaking is low for {asset}, so it "
       "can keep running.", "keep_running", 1.0, 0.8),
      ("Temperature is normal. The heat is low, so {asset} can keep "
       "running.", "keep_running", 1.0, 0.7),
      ("Filter was changed recently. The filter is new, so the risk "
       "is low for {asset}.", "keep_running", 0.5, 0.6)],
     "schedule"),
    ("Should {asset} be taken offline now for maintenance?",
     [("Imbalance 2.1 mm/s. The imbalance is low for {asset} and "
       "within the limit.", "keep_running", 1.5, 0.8),
      ("Within ISO limit. {asset} is within the limit, so it can keep "
       "running.", "keep_running", 2.0, 0.9),
      ("No temperature rise. The heat is low for {asset}, so the risk "
       "is low.", "keep_running", 1.0, 0.8),
      ("Slight hum from {asset}. The hum should be monitored and the "
       "vibration checked.", "schedule", 1.0, 0.7),
      ("Blades were inspected. The blades are fine, so {asset} can "
       "keep running.", "keep_running", 0.5, 0.6)],
     "keep_running"),
    ("Should {asset} be taken offline now for maintenance?",
     [("Leak at the seal. The leak is severe for {asset}, so "
       "maintenance should happen now.", "offline_now", 2.0, 0.9),
      ("Pressure is fluctuating. The pressure is unstable for {asset}, "
       "so the risk of failure is high.", "offline_now", 2.0, 0.9),
      ("Fluid level is dropping. The level is low, so {asset} should "
       "be checked at once.", "offline_now", 1.0, 0.8),
      ("Safety risk is present. The risk is severe, so {asset} should "
       "be taken offline.", "offline_now", 1.0, 0.8),
      ("Production can pause. The pause means scheduled maintenance "
       "for {asset} is possible.", "schedule", 0.5, 0.6)],
     "offline_now"),
]

RESEARCH = [
    ("Does {method} outperform {baseline} on {task}?",
     [("{method} accuracy is 4.2 points better than {baseline} on "
       "{task}. The result shows {method} can outperform the baseline.",
       "yes", 2.0, 0.9),
      ("{method} F1 is 3.1 points better than {baseline} on {task}. "
       "The F1 score shows {method} is stronger.", "yes", 2.0, 0.9),
      ("Ablation confirms the gain. The ablation shows {method} beats "
       "{baseline} because of its new design.", "yes", 1.0, 0.8),
      ("Only one dataset was used. A single dataset means the result "
       "for {task} is inconclusive.", "inconclusive", 1.0, 0.7),
      ("No significance test was run. Without a test, the claim that "
       "{method} can outperform {baseline} is weaker.",
       "inconclusive", 0.5, 0.6)],
     "yes"),
    ("Does {method} outperform {baseline} on {task}?",
     [("{method} accuracy is 1.0 point better than {baseline} on "
       "{task}. The gain is small but {method} is stronger.", "yes",
       1.0, 0.8),
      ("{method} latency is 3 times worse than {baseline} on {task}. "
       "The latency shows {method} is weaker in practice.", "no",
       2.0, 0.9),
      ("No ablation was run. Without an ablation, the result for "
       "{method} on {task} is inconclusive.", "inconclusive", 2.0, 0.8),
      ("Two datasets were used. Two datasets show {method} beats "
       "{baseline} twice.", "yes", 1.0, 0.7),
      ("{baseline} is outdated. An outdated baseline means the "
       "comparison on {task} is inconclusive.", "inconclusive", 1.0, 0.7)],
     "inconclusive"),
    ("Does {method} outperform {baseline} on {task}?",
     [("Replication scored 2.0 points worse than {baseline} on "
       "{task}. The replication shows {method} is weaker.", "no",
       2.0, 0.9),
      ("The original used a different split. A different split means "
       "{method} did not beat {baseline} fairly.", "no", 1.5, 0.8),
      ("Code is unavailable. Without code, the claim that {method} "
       "can outperform {baseline} cannot be checked.", "no", 1.0, 0.7),
      ("One positive anecdote exists. The anecdote shows {method} "
       "beat {baseline} once on {task}.", "yes", 1.0, 0.6),
      ("Metrics are incomparable. Incomparable metrics make the "
       "result on {task} inconclusive.", "inconclusive", 1.0, 0.7)],
     "no"),
    ("Does {method} outperform {baseline} on {task}?",
     [("{method} is 5 points better than {baseline} on dataset A. "
       "The result shows {method} can outperform the baseline.",
       "yes", 2.0, 0.9),
      ("{method} is 3 points better than {baseline} on dataset B. "
       "The gain shows {method} is stronger.", "yes", 2.0, 0.9),
      ("{method} is 2 points better than {baseline} on dataset C. "
       "The gain shows {method} beats {baseline} again.", "yes",
       1.0, 0.8),
      ("Significance p is below 0.01. The test shows {method} beats "
       "{baseline} on {task} for real.", "yes", 1.0, 0.9),
      ("Compute cost is high. High cost shows {method} is weaker in "
       "practice than {baseline}.", "no", 1.0, 0.6)],
     "yes"),
    ("Does {method} outperform {baseline} on {task}?",
     [("{method} is 1 point better than {baseline} on dataset A. The "
       "gain is small for {task}.", "yes", 1.0, 0.7),
      ("{method} is 1 point worse than {baseline} on dataset B. The "
       "loss shows {method} is weaker there.", "no", 1.0, 0.7),
      ("Only 30 samples were used. A small sample means the result "
       "on {task} is inconclusive.", "inconclusive", 2.0, 0.8),
      ("No error bars were reported. Without error bars, the claim "
       "that {method} can outperform {baseline} is weaker.",
       "inconclusive", 1.5, 0.8),
      ("This is a pilot study. A pilot study means the result on "
       "{task} is inconclusive.", "inconclusive", 1.0, 0.7)],
     "inconclusive"),
    ("Does {method} outperform {baseline} on {task}?",
     [("{method} accuracy is 6 points worse than {baseline} on "
       "{task}. The result shows {method} is weaker.", "no", 2.0, 0.9),
      ("{method} is slower than {baseline}. Being slower shows "
       "{method} is weaker in practice.", "no", 1.5, 0.8),
      ("{method} has more parameters than {baseline}. More parameters "
       "show {method} is weaker for {task}.", "no", 1.0, 0.7),
      ("One niche win exists. The win shows {method} beat {baseline} "
       "once on {task}.", "yes", 1.0, 0.6),
      ("The authors agree. The authors show {method} is weaker than "
       "{baseline}.", "no", 0.5, 0.7)],
     "no"),
    ("Does {method} outperform {baseline} on {task}?",
     [("{method} F1 is 4 points better than {baseline} on {task}. "
       "The F1 score shows {method} is stronger.", "yes", 2.0, 0.9),
      ("Accuracy is equal. Equal accuracy means the result on {task} "
       "is inconclusive.", "inconclusive", 1.0, 0.7),
      ("{method} recall is 6 points better than {baseline}. The "
       "recall shows {method} beats {baseline}.", "yes", 1.5, 0.8),
      ("{method} precision is 1 point worse than {baseline}. Lower "
       "precision shows {method} is weaker there.", "no", 1.0, 0.7),
      ("Two datasets agree. Two datasets show {method} beats "
       "{baseline} on {task}.", "yes", 1.0, 0.8)],
     "yes"),
    ("Does {method} outperform {baseline} on {task}?",
     [("{method} reports 91 percent alone. Reporting alone means the "
       "result on {task} is inconclusive.", "inconclusive", 2.0, 0.8),
      ("No baseline was run. Without {baseline}, the claim that "
       "{method} can outperform anything is inconclusive.",
       "inconclusive", 2.0, 0.8),
      ("The method is novel. A novel method shows {method} is "
       "stronger in design.", "yes", 1.0, 0.7),
      ("The dataset is private. A private dataset means the result "
       "on {task} is inconclusive.", "inconclusive", 1.0, 0.7),
      ("The paper claims state of the art. The claim shows {method} "
       "beats {baseline} on {task}.", "yes", 0.5, 0.6)],
     "inconclusive"),
]

HEALTH_NAMES = ["Aisha", "Bilal", "Chen", "Dania", "Emeka", "Fatima",
                "Gul", "Hassan", "Iqra", "Junaid", "Kiran", "Laila",
                "Musa", "Nadia", "Omar", "Priya"]
PHM_ASSETS = ["turbine T-7", "pump P-3", "compressor C-12", "motor M-5",
              "gearbox G-9", "fan F-2", "hydraulic unit H-8",
              "conveyor K-4", "turbine T-11", "pump P-8",
              "compressor C-4", "motor M-9", "gearbox G-2", "fan F-7",
              "hydraulic unit H-3", "conveyor K-9"]
RESEARCH_METHODS = [
    ("SparseAttn", "DenseAttn", "summarization"),
    ("GraphRouter", "FlatRouter", "question answering"),
    ("LiteBERT", "BERT-base", "sentiment analysis"),
    ("NeuroSketch", "SketchBase", "code completion"),
    ("TinyViT", "ResNet-50", "image classification"),
    ("EchoLM", "BaseLM", "dialogue generation"),
    ("FastRank", "BM25", "passage retrieval"),
    ("CalibNet", "Platt", "confidence calibration"),
    ("SparseAttn-v2", "DenseAttn", "summarization"),
    ("GraphRouter-v2", "FlatRouter", "question answering"),
    ("LiteBERT-v2", "BERT-base", "sentiment analysis"),
    ("NeuroSketch-v2", "SketchBase", "code completion"),
    ("TinyViT-v2", "ResNet-50", "image classification"),
    ("EchoLM-v2", "BaseLM", "dialogue generation"),
    ("FastRank-v2", "BM25", "passage retrieval"),
    ("CalibNet-v2", "Platt", "confidence calibration"),
]


def _argmax_gold(evidence) -> str:
    totals = {}
    for _text, supports, weight, _strength in evidence:
        if supports == "none":
            continue
        totals[supports] = totals.get(supports, 0.0) + weight
    best = max(totals.values())
    return sorted(a for a, w in totals.items() if w == best)[0]


def build() -> list:
    """Build all 48 cases; returns JSON-serializable dicts."""
    out = []
    domains = [
        ("health", "H", HEALTH, [{"name": n} for n in HEALTH_NAMES]),
        ("phm", "P", PHM, [{"asset": a} for a in PHM_ASSETS]),
        ("research", "R", RESEARCH,
         [{"method": m, "baseline": b, "task": t}
          for m, b, t in RESEARCH_METHODS]),
    ]
    for domain, prefix, templates, slot_sets in domains:
        assert len(templates) == 8 and len(slot_sets) == 16
        for i, slots in enumerate(slot_sets):
            template = templates[i % 8]
            question_t, evidence_t, gold = template
            evidence = []
            for j, (text_t, supports, weight, strength) in enumerate(evidence_t):
                evidence.append(Evidence(
                    "%s%d" % (prefix, j + 1), text_t.format(**slots),
                    supports, weight, strength))
            assert _argmax_gold(evidence_t) == gold, \
                "%s template %d gold mismatch" % (domain, i % 8)
            case = Case("%s-%02d" % (prefix, i + 1), domain,
                        question_t.format(**slots), evidence, gold)
            claims = explain_stable(case).claims
            out.append({
                "case_id": case.case_id,
                "domain": case.domain,
                "question": case.question,
                "evidence": [
                    {"id": e.id, "text": e.text, "supports": e.supports,
                     "weight": e.weight, "strength": e.strength}
                    for e in case.evidence
                ],
                "gold_answer": case.gold_answer,
                "gold_claims": [
                    {"text": c.text, "evidence_ids": c.evidence_ids,
                     "confidence": c.confidence, "stance": c.stance}
                    for c in claims
                ],
            })
    return out


def main() -> None:
    cases = build()
    path = ROOT / "data" / "cases.json"
    path.write_text(json.dumps(cases, indent=2), encoding="utf-8")
    print("Wrote %d cases to %s" % (len(cases), path))
    domains = sorted({c["domain"] for c in cases})
    for d in domains:
        golds = [c["gold_answer"] for c in cases if c["domain"] == d]
        print("  %s: %d cases, gold answers %s"
              % (d, len(golds), sorted(set(golds))))


if __name__ == "__main__":
    main()
