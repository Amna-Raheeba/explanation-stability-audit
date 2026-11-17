"""Streamlit dashboard: explore explanation stability audits.

Three tabs:
1. Case Explorer — one case under one agent: baseline explanation,
   per-perturbation paradox rates, per-claim survival.
2. Paradox Analysis — per-agent and per-kind paradox rates, and the
   breaker table (which perturbation breaks which agent).
3. Evaluation — the full aggregate table over all 48 cases.

Run: ``streamlit run app.py``.
"""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from explanation_stability_audit.audit import audit_case  # noqa: E402
from explanation_stability_audit.evaluation import (  # noqa: E402
    evaluate,
    load_cases,
)
from explanation_stability_audit.explainers import AGENTS, explain  # noqa: E402
from explanation_stability_audit.models import PerturbationKind  # noqa: E402


@st.cache_data
def _cases():
    return load_cases(ROOT / "data" / "cases.json")


@st.cache_data
def _evaluation():
    return evaluate(_cases())


st.title("Explanation Stability Audit")
st.write(
    "Does an agent's explanation survive perturbations that leave its "
    "answer unchanged? If the reasons flip while the answer holds, the "
    "explanation is not the real reason. The paradox rate measures "
    "exactly that."
)

cases = _cases()
case_ids = [c.case_id for c in cases]
tab1, tab2, tab3 = st.tabs(
    ["Case Explorer", "Paradox Analysis", "Evaluation"])

with tab1:
    case_id = st.selectbox("Case", case_ids, index=0)
    agent = st.selectbox("Agent", list(AGENTS), index=1)
    case = next(c for c in cases if c.case_id == case_id)
    st.subheader("%s [%s]" % (case.case_id, case.domain))
    st.write(case.question)
    explanation = explain(case, agent)
    audit = audit_case(case, agent)
    st.metric("Verdict", audit.verdict)
    col1, col2, col3 = st.columns(3)
    col1.metric("Paradox rate", "%.3f" % audit.paradox_rate)
    col2.metric("Semantic paradox", "%.3f" % audit.paradox_rate_semantic)
    col3.metric("Answer stability", "%.3f" % audit.answer_stability)
    st.subheader("Baseline explanation — answer: %s" % explanation.answer)
    for claim in explanation.claims:
        st.write("- %s (confidence %.2f)" % (claim.text, claim.confidence))
    st.subheader("Per-claim survival")
    st.table([{
        "claim": cs.claim_text,
        "survival": round(cs.survival_rate, 2),
        "broken by": cs.breaker or "nothing",
    } for cs in audit.claim_stability])
    st.subheader("Per-perturbation paradox rate")
    st.table([{
        "perturbation": kind.label,
        "paradox": round(audit.per_kind[kind.value]["paradox_rate"], 3),
        "answer": round(audit.per_kind[kind.value]["answer_stability"], 3),
    } for kind in PerturbationKind])

with tab2:
    _audits, summaries, headline = _evaluation()
    st.subheader("Semantic paradox rate by agent")
    st.table([{
        "agent": agent,
        "paradox (semantic)": round(s.mean_paradox_rate_semantic, 3),
        "paradox (all)": round(s.mean_paradox_rate, 3),
        "explanation stability": round(s.mean_explanation_stability, 3),
        "verdicts": str(dict(sorted(s.verdict_counts.items()))),
    } for agent, s in summaries.items()])
    st.subheader("Per-kind paradox rate by agent")
    st.table([{
        "perturbation": kind.label,
        **{agent: round(s.per_kind_paradox[kind.value], 3)
           for agent, s in summaries.items()},
    } for kind in PerturbationKind])
    st.write("Headline paradox gap: %.3f" % headline["paradox_gap"])

with tab3:
    _audits, summaries, _headline = _evaluation()
    rows = [{
        "case": a.case_id,
        "agent": a.agent,
        "verdict": a.verdict,
        "paradox": round(a.paradox_rate, 3),
        "semantic": round(a.paradox_rate_semantic, 3),
        "answer": round(a.answer_stability, 3),
        "breaker": a.breaker or "",
    } for a in _audits]
    st.table(rows)
