"""Deterministic perturbations of a case.

Every perturbation is a pure function of (case, seed): same seed,
same output. The synonym map is the single source of truth for
word-level changes, so the stable explainer can canonicalize the
same words back — that is what makes it stable by design, and what
makes the keyword-fragile agent fragile.
"""

from __future__ import annotations

import random
import re

from .models import Case, Evidence, PerturbationKind

# Word-level synonyms used by paraphrase (question) and synonym_swap
# (evidence). Applied left to right; each word replaced at most once.
SYNONYMS = {
    "risk": "danger",
    "danger": "risk",
    "patient": "person",
    "person": "patient",
    "likely": "probable",
    "probable": "likely",
    "increase": "raise",
    "raise": "increase",
    "severe": "serious",
    "serious": "severe",
    "check": "examine",
    "examine": "check",
    "cause": "trigger",
    "trigger": "cause",
    "high": "elevated",
    "elevated": "high",
    "low": "reduced",
    "reduced": "low",
    "show": "indicate",
    "indicate": "show",
    "fail": "break down",
    "urgent": "immediate",
    "immediate": "urgent",
    "outperform": "beat",
    "beat": "outperform",
    "better": "stronger",
    "stronger": "better",
    "worse": "weaker",
    "weaker": "worse",
    "vibration": "shaking",
    "shaking": "vibration",
    "temperature": "heat",
    "heat": "temperature",
    "recommend": "advise",
    "advise": "recommend",
    "should": "ought to",
    "monitor": "watch",
    "watch": "monitor",
}

# Irrelevant passages injected by the irrelevant_injection perturbation.
# They support no answer (weight 0) and must never enter an explanation.
IRRELEVANT = {
    "health": Evidence(
        "X1",
        "The cafeteria serves lunch from 11:30 to 14:00 on weekdays.",
        "none", 0.0, 0.5,
    ),
    "phm": Evidence(
        "X1",
        "The staff car park has 40 spaces and a new coat of paint.",
        "none", 0.0, 0.5,
    ),
    "research": Evidence(
        "X1",
        "The conference dinner is served at 19:00 in the main hall.",
        "none", 0.0, 0.5,
    ),
}

_WORD_RE = re.compile(r"[A-Za-z]+")


def _substitute_words(text: str) -> str:
    """Replace every mapped word once, preserving initial capitals."""

    def repl(match: "re.Match[str]") -> str:
        word = match.group(0)
        key = word.lower()
        if key not in SYNONYMS:
            return word
        new = SYNONYMS[key]
        if word[:1].isupper():
            new = new[:1].upper() + new[1:]
        return new

    return _WORD_RE.sub(repl, text)


# Referent substitution: a real paraphrase replaces the subject with a
# pronoun-like referent ("patient Aisha" -> "this patient"). Without
# it, paraphrase only swaps a couple of verbs and every agent that
# anchors on proper nouns looks stable for free.
_REFERENT_RES = [
    (re.compile(r"patient [A-Z][a-z]+"), "this patient"),
    (re.compile(r"(turbine|pump|compressor|motor|gearbox|fan|hydraulic unit|conveyor) [A-Z]-\d+"),
     "this unit"),
    (re.compile(r"Does (\S+) outperform"), "Does the new method outperform"),
]


def _substitute_referents(text: str) -> str:
    for pattern, replacement in _REFERENT_RES:
        text = pattern.sub(replacement, text)
    return text


def _typo_word(word: str, rng: random.Random) -> str:
    """Swap two adjacent interior letters of one word, once."""
    if len(word) < 4:
        return word
    i = rng.randint(1, len(word) - 3)
    chars = list(word)
    chars[i], chars[i + 1] = chars[i + 1], chars[i]
    return "".join(chars)


def _typo_text(text: str, rng: random.Random) -> str:
    words = text.split(" ")
    long_words = [i for i, w in enumerate(words) if len(w) >= 5]
    if not long_words:
        return text
    for idx in rng.sample(long_words, min(2, len(long_words))):
        words[idx] = _typo_word(words[idx], rng)
    return " ".join(words)


def apply_perturbation(case: Case, kind: PerturbationKind, seed: int) -> Case:
    """Return a perturbed copy of ``case`` (the original is untouched)."""
    kind = PerturbationKind(kind)  # ValueError on an unknown kind
    rng = random.Random("%s:%s:%d" % (case.case_id, kind.value, seed))
    new_id = "%s~%s" % (case.case_id, kind.value)
    if kind == PerturbationKind.REPEAT_QUERY:
        return Case(new_id, case.domain, case.question, list(case.evidence),
                    case.gold_answer, list(case.gold_claims))
    if kind == PerturbationKind.PARAPHRASE:
        question = _substitute_referents(case.question)
        return Case(new_id, case.domain, _substitute_words(question),
                    list(case.evidence), case.gold_answer,
                    list(case.gold_claims))
    if kind == PerturbationKind.SYNONYM_SWAP:
        ev = [Evidence(e.id, _substitute_words(e.text), e.supports,
                       e.weight, e.strength) for e in case.evidence]
        return Case(new_id, case.domain, case.question, ev,
                    case.gold_answer, list(case.gold_claims))
    if kind == PerturbationKind.REORDER_EVIDENCE:
        ev = list(case.evidence)
        rng.shuffle(ev)
        return Case(new_id, case.domain, case.question, ev,
                    case.gold_answer, list(case.gold_claims))
    if kind == PerturbationKind.TYPO_NOISE:
        return Case(new_id, case.domain, _typo_text(case.question, rng),
                    list(case.evidence), case.gold_answer,
                    list(case.gold_claims))
    if kind == PerturbationKind.IRRELEVANT_INJECTION:
        extra = IRRELEVANT.get(case.domain, IRRELEVANT["health"])
        return Case(new_id, case.domain, case.question,
                    list(case.evidence) + [extra], case.gold_answer,
                    list(case.gold_claims))
    if kind == PerturbationKind.DROP_WEAK_EVIDENCE:
        if len(case.evidence) <= 1:
            return Case(new_id, case.domain, case.question,
                        list(case.evidence), case.gold_answer,
                        list(case.gold_claims))
        weakest = min(case.evidence,
                      key=lambda e: (e.weight, e.strength, e.id))
        ev = [e for e in case.evidence if e.id != weakest.id]
        return Case(new_id, case.domain, case.question, ev,
                    case.gold_answer, list(case.gold_claims))
    if kind == PerturbationKind.TRUNCATE_EVIDENCE:
        ev = [e.truncated() for e in case.evidence]
        return Case(new_id, case.domain, case.question, ev,
                    case.gold_answer, list(case.gold_claims))
    raise ValueError("unknown perturbation kind: %r" % (kind,))
