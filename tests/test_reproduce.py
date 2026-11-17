"""Tests for the reproduce-results script (drift guard)."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import reproduce_results  # noqa: E402


def test_reproduce_regenerates_matching_results(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    assert reproduce_results.main() == 0
    data = json.loads(
        (ROOT / "results" / "evaluation.json").read_text())
    assert len(data["rows"]) == 192
    assert data["headline"]["stable_paradox_rate_semantic"] == 0.0
