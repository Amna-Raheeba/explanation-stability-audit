"""Four deterministic explainer agents.

Each agent derives an answer and an explanation from a case's
evidence, with no model call. They differ only in *how* they read
the evidence, which is exactly what the audit measures:

- ``stable``: sums weights over all passages, cites in id order,
  canonicalizes synonyms before quoting. Robust by design.
- ``order_sensitive``: only the first two passages in list order
  count (primacy bias). Reordering the evidence rewrites its reasons.
- ``keyword_fragile``: matches raw question keywords against passage
  text, no canonicalization, no stemming. Paraphrase, synonyms and
  typos drop its matches.
- ``confident``: the stable agent's answer, but it cites *every*
  passage (including irrelevant ones) at confidence 0.95. Its
  confidence never moves; its reasons do.
"""

from __future__ import annotations

from typing import Dict, List

from .models import Case, Claim, Evidence, Explanation, normalize_text
from .perturbations import SYNONYMS

AGENTS = ("stable", "order_sensitive", "keyword_fragile", "confident")

STOPWORDS = frozenset(
    {
        "should", "the", "a", "an", "is", "this", "be", "to", "for",
        "of", "and", "or", "does", "do", "what", "how", "when",
        "than", "then", "with", "by", "in", "on", "at", "it", "its",
    }
)

# Canonical form for each synonym pair: the alphabetically first word.
# The stable agent quotes canonical text, so a paraphrase that swaps
# "risk" for "danger" maps back to the same claim.
_CANONICAL: Dict[str, str] = {}
for _a, _b in SYNONYMS.items():
    _CANONICAL[_a] = min(_a, _b)


def canonicalize(text: str) -> str:
    """Map every synonym in ``text`` to its canonical form."""
    out = []
    for word in text.split(" "):
        key = word.lower().strip(".,;:!?")
        out.append(_CANONICAL.get(key, word))
    return " ".join(out)


def _quote(evidence: Evidence, canonical: bool) -> str:
    text = canonicalize(evidence.text) if canonical else evidence.text
    words = text.split(" ")[:8]
    return " ".join(words)


def _argmax_answer(weights: Dict[str, float]) -> str:
    """Best-supported answer; ties break alphabetically (deterministic)."""
    if not weights:
        return "abstain"
    best = max(weights.values())
    winners = sorted(a for a, w in weights.items() if w == best)
    return winners[0]


def _weights(evidence: List[Evidence]) -> Dict[str, float]:
    totals: Dict[str, float] = {}
    for ev in evidence:
        if ev.supports == "none":
            continue
        totals[ev.supports] = totals.get(ev.supports, 0.0) + ev.weight
    return totals


def _claim(evidence: Evidence, answer: str, canonical: bool,
           confidence: float) -> Claim:
    text = "%s supports %s: %s" % (evidence.id, answer, _quote(evidence, canonical))
    return Claim(text, [evidence.id], confidence, stance=answer)


def explain_stable(case: Case) -> Explanation:
    """Order-, paraphrase- and injection-invariant by construction."""
    answer = _argmax_answer(_weights(case.evidence))
    claims = [
        _claim(ev, answer, True, ev.strength)
        for ev in sorted(case.evidence, key=lambda e: e.id)
        if ev.supports == answer and ev.weight >= 1.0
    ]
    return Explanation(answer, claims)


def explain_order_sensitive(case: Case) -> Explanation:
    """Only the first two passages in list order count."""
    window = case.evidence[:2]
    answer = _argmax_answer(_weights(window))
    claims = [
        _claim(ev, answer, False, ev.strength)
        for ev in window
        if ev.supports == answer and ev.weight >= 1.0
    ]
    return Explanation(answer, claims)


def _keywords(question: str) -> frozenset:
    words = normalize_text(question).split(" ")
    return frozenset(w for w in words if w and w not in STOPWORDS)


def explain_keyword_fragile(case: Case) -> Explanation:
    """Exact raw keyword overlap between question and passage text.

    A passage counts only if it shares at least two question
    keywords: a single shared word (usually just the patient's name)
    is not engagement with the question. That threshold is what makes
    the agent fragile to paraphrase and synonym swaps, which strip
    one shared word at a time.

    Confidence is strength times the overlap ratio (matched question
    keywords over all question keywords), so it *moves* when a
    paraphrase or typo thins the match — unlike the confident agent,
    whose confidence never moves at all.
    """
    keywords = _keywords(case.question)
    matched = [
        ev for ev in case.evidence
        if len(keywords & set(normalize_text(ev.text).split(" "))) >= 2
    ]
    answer = _argmax_answer(_weights(matched))
    claims = []
    for ev in matched:
        if ev.supports == answer and ev.weight >= 1.0:
            overlap = len(keywords & set(normalize_text(ev.text).split(" ")))
            ratio = overlap / len(keywords) if keywords else 0.0
            claims.append(_claim(ev, answer, False, ev.strength * ratio))
    return Explanation(answer, claims)


def explain_confident(case: Case) -> Explanation:
    """Stable answer, but cites every passage at confidence 0.95."""
    answer = _argmax_answer(_weights(case.evidence))
    claims = [
        _claim(ev, ev.supports, False, 0.95) for ev in case.evidence
    ]
    return Explanation(answer, claims)


def explain(case: Case, agent: str) -> Explanation:
    """Run one agent on one case."""
    if agent == "stable":
        return explain_stable(case)
    if agent == "order_sensitive":
        return explain_order_sensitive(case)
    if agent == "keyword_fragile":
        return explain_keyword_fragile(case)
    if agent == "confident":
        return explain_confident(case)
    raise ValueError("unknown agent: %r" % (agent,))
