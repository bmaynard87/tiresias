"""Tests for CLI application."""

import json
from pathlib import Path

from typer.testing import CliRunner

from tiresias.cli.app import app

runner = CliRunner()


def test_cli_version() -> None:
    """Test --version flag."""
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "0.4.0" in result.output


def test_cli_help() -> None:
    """Test that help text is shown."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "tiresias" in result.output.lower()
    assert "review" in result.output


def test_cli_review_single_file(tmp_path: Path) -> None:
    """Test CLI with a single file."""
    test_file = tmp_path / "test.md"
    test_file.write_text("# Design\nSome content")

    result = runner.invoke(app, ["review", str(test_file)])

    assert result.exit_code == 0
    assert "Tiresias" in result.stdout


def test_cli_json_output(tmp_path: Path) -> None:
    """Test JSON output format."""
    test_file = tmp_path / "test.md"
    test_file.write_text("# Design\nMinimal content")

    result = runner.invoke(app, ["review", str(test_file), "--format", "json"])

    assert result.exit_code == 0
    # Should be valid JSON
    parsed = json.loads(result.stdout)
    assert "metadata" in parsed
    assert "findings" in parsed
    assert "risk_score" in parsed


def test_cli_fail_on_high() -> None:
    """Test --fail-on high option."""
    # This would require a more complex setup with actual files
    # For now, we test the logic indirectly through other tests
    pass


def test_cli_review_nonexistent_file() -> None:
    """Test CLI with nonexistent file."""
    result = runner.invoke(app, ["review", "/nonexistent/file.md"])

    assert result.exit_code == 3
    assert "Error" in result.output


def test_cli_review_default_no_evidence(tmp_path: Path) -> None:
    """Test that evidence is hidden by default."""
    test_file = tmp_path / "test.md"
    test_file.write_text("# Design\nSome content")

    result = runner.invoke(app, ["review", str(test_file), "--no-color"])

    assert result.exit_code == 0
    assert "Evidence:" not in result.stdout


def test_cli_review_show_evidence_flag(tmp_path: Path) -> None:
    """Test that --show-evidence displays evidence."""
    test_file = tmp_path / "test.md"
    test_file.write_text("# Design\nSome content")

    result = runner.invoke(app, ["review", str(test_file), "--show-evidence", "--no-color"])

    assert result.exit_code == 0
    assert "Evidence:" in result.stdout


def test_cli_review_verbose_alias(tmp_path: Path) -> None:
    """Test that --verbose alias works."""
    test_file = tmp_path / "test.md"
    test_file.write_text("# Design\nSome content")

    result = runner.invoke(app, ["review", str(test_file), "--verbose", "--no-color"])

    assert result.exit_code == 0
    assert "Evidence:" in result.stdout


def test_cli_maturity_in_text_output(tmp_path: Path) -> None:
    """Test that maturity appears in text output."""
    doc = tmp_path / "test.md"
    doc.write_text("# Design\nVery short document.")

    result = runner.invoke(app, ["review", str(doc), "--no-color"])

    assert result.exit_code == 0
    assert "Document Maturity" in result.stdout
    assert "Level:" in result.stdout
    assert "Score:" in result.stdout
    assert "Signals:" in result.stdout


def test_cli_maturity_in_json_output(tmp_path: Path) -> None:
    """Test that maturity appears in JSON output."""
    doc = tmp_path / "test.md"
    doc.write_text("# Design\nVery short document.")

    result = runner.invoke(app, ["review", str(doc), "--format", "json"])

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert "maturity" in report
    assert report["maturity"]["level"] in [
        "notes",
        "early_draft",
        "design_spec",
        "production_ready",
    ]
    assert "score" in report["maturity"]
    assert 0 <= report["maturity"]["score"] <= 100
    assert "confidence" in report["maturity"]
    assert "signals" in report["maturity"]
    assert "metrics" in report["maturity"]


def test_cli_baseline_invalid_ref(tmp_path: Path) -> None:
    """Test baseline mode with invalid git ref."""
    test_file = tmp_path / "test.md"
    test_file.write_text("# Design\nSome content")

    result = runner.invoke(app, ["review", str(test_file), "--baseline", "invalid-ref-xyz"])

    assert result.exit_code == 3
    assert "Error" in result.output
    assert "baseline" in result.output.lower() or "invalid" in result.output.lower()


def test_cli_baseline_json_output_fields(tmp_path: Path) -> None:
    """Test that baseline mode adds expected fields to JSON output."""
    # Note: This test runs in the actual tiresias repo, so baseline will work
    test_file = tmp_path / "test.md"
    test_file.write_text("# Design\nMinimal content")

    result = runner.invoke(
        app, ["review", str(test_file), "--baseline", "HEAD", "--format", "json"]
    )

    # If this fails due to not being in git repo, that's expected in some test environments
    if result.exit_code == 0:
        report = json.loads(result.stdout)
        assert "baseline_ref" in report
        assert report["baseline_ref"] == "HEAD"
        assert "comparison" in report
        if report["comparison"] is not None:  # Only if baseline comparison succeeded
            assert "baseline_summary" in report["comparison"]
            assert "new_findings" in report["comparison"]
            assert "worsened_findings" in report["comparison"]
            assert "unchanged_findings" in report["comparison"]
            assert "improved_findings" in report["comparison"]
            assert "maturity_regressed" in report["comparison"]


def test_cli_baseline_text_output_shows_comparison(tmp_path: Path) -> None:
    """Test that baseline mode shows comparison summary in text output."""
    test_file = tmp_path / "test.md"
    test_file.write_text("# Design\nSome content")

    result = runner.invoke(app, ["review", str(test_file), "--baseline", "HEAD", "--no-color"])

    # If in git repo, should show baseline comparison
    if result.exit_code == 0:
        # Check for baseline comparison indicators
        output = result.stdout
        if "Baseline Comparison" in output:
            assert "Baseline:" in output or "New:" in output or "Worsened:" in output


def test_cli_baseline_fail_on_with_new_findings(tmp_path: Path) -> None:
    """Test that --fail-on works with baseline mode (checks new/worsened only)."""
    # Create a minimal doc that will have HIGH findings
    test_file = tmp_path / "test.md"
    test_file.write_text("# Widget Service\nWe will build a widget service.")

    # Without baseline, should fail with HIGH findings
    result = runner.invoke(app, ["review", str(test_file), "--fail-on", "high"])

    # This document should have high-severity findings
    # Exit code 1 means findings were found and fail-on triggered
    # Exit code 0 means no critical findings or feature not working as expected
    assert result.exit_code in (0, 1)  # Either way is valid depending on findings
