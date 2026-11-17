"""Dashboard test via Streamlit AppTest."""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_dashboard_runs_without_exception():
    at = AppTest.from_file(APP)
    at.run()
    assert not at.exception


def test_dashboard_has_three_tabs():
    at = AppTest.from_file(APP)
    at.run()
    assert len(at.tabs) == 3
    labels = [t.label for t in at.tabs]
    assert labels == ["Case Explorer", "Paradox Analysis", "Evaluation"]
