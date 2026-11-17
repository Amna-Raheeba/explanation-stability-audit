"""Tests for the command-line interface."""

from explanation_stability_audit.cli import main


def test_cli_demo(capsys):
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "stable" in out and "paradox" in out


def test_cli_evaluate(tmp_path, capsys):
    assert main(["evaluate", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "evaluation.json").exists()
    out = capsys.readouterr().out
    assert "192 audits" in out


def test_cli_audit(capsys):
    assert main(["audit", "--case", "H-01", "--agent", "stable"]) == 0
    out = capsys.readouterr().out
    assert "H-01" in out and "Audit verdict" in out


def test_cli_audit_unknown_case():
    assert main(["audit", "--case", "ZZ-99", "--agent", "stable"]) == 2


def test_cli_perturb(capsys):
    assert main(["perturb", "--case", "H-01", "--kind", "paraphrase"]) == 0
    out = capsys.readouterr().out
    assert "Perturbed" in out
    question_line = [line for line in out.splitlines()
                     if line.startswith("Perturbed")][0]
    assert "Aisha" not in question_line
    assert "this person" in question_line


def test_cli_perturb_unknown_case():
    assert main(["perturb", "--case", "ZZ-99", "--kind", "paraphrase"]) == 2
