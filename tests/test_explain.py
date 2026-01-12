"""Tests for explain command."""

import json
from pathlib import Path

from typer.testing import CliRunner

from tiresias.cli.app import app

runner = CliRunner()


def test_explain_known_rule_text() -> None:
    """Test explaining a known rule in text format."""
    result = runner.invoke(app, ["explain", "REQ-001"])

    assert result.exit_code == 0
    assert "REQ-001" in result.stdout
    assert "Missing success metrics" in result.stdout
    assert "Requirements" in result.stdout or "requirements" in result.stdout
    assert "High" in result.stdout or "high" in result.stdout
    assert "What it checks:" in result.stdout
    assert "Why it matters:" in result.stdout
    assert "How to address it:" in result.stdout


def test_explain_known_rule_json() -> None:
    """Test explaining a known rule in JSON format."""
    result = runner.invoke(app, ["explain", "REQ-001", "--format", "json"])

    assert result.exit_code == 0

    # Parse and validate JSON
    parsed = json.loads(result.stdout)
    assert parsed["id"] == "REQ-001"
    assert parsed["title"] == "Missing success metrics"
    assert parsed["severity"] == "high"
    assert parsed["category"] == "requirements"
    assert "checks" in parsed
    assert "why" in parsed
    assert "how_to_fix" in parsed
    assert "pitfalls" in parsed


def test_explain_unknown_rule() -> None:
    """Test explaining an unknown rule ID."""
    result = runner.invoke(app, ["explain", "INVALID-999"])

    assert result.exit_code == 3
    assert "INVALID-999" in result.output
    assert "--list" in result.output or "explain --list" in result.output


def test_explain_list_text() -> None:
    """Test listing all rules in text format."""
    result = runner.invoke(app, ["explain", "--list"])

    assert result.exit_code == 0
    assert "Available Rules" in result.stdout

    # Check for all 12 rule IDs
    expected_rules = [
        "REQ-001",
        "REQ-002",
        "REQ-003",
        "ARCH-001",
        "ARCH-002",
        "ARCH-003",
        "TEST-001",
        "OPS-001",
        "OPS-002",
        "SEC-001",
        "PERF-001",
        "DOC-001",
    ]
    for rule_id in expected_rules:
        assert rule_id in result.stdout

    assert "Rule ID" in result.stdout or "rule" in result.stdout.lower()
    assert "Title" in result.stdout or "title" in result.stdout.lower()


def test_explain_list_json() -> None:
    """Test listing all rules in JSON format."""
    result = runner.invoke(app, ["explain", "--list", "--format", "json"])

    assert result.exit_code == 0

    # Parse and validate JSON
    parsed = json.loads(result.stdout)
    assert "rules" in parsed
    assert len(parsed["rules"]) == 12

    # Check structure of first rule
    first_rule = parsed["rules"][0]
    assert "id" in first_rule
    assert "title" in first_rule


def test_explain_no_args_no_list() -> None:
    """Test explain with no arguments and no --list flag."""
    result = runner.invoke(app, ["explain"])

    assert result.exit_code == 2
    assert "Error" in result.output or "error" in result.output.lower()
    assert "rule ID" in result.output or "RULE_ID" in result.output


def test_explain_output_to_file(tmp_path: Path) -> None:
    """Test writing explain output to a file."""
    output_file = tmp_path / "explanation.txt"
    result = runner.invoke(app, ["explain", "REQ-001", "--output", str(output_file)])

    assert result.exit_code == 0
    assert output_file.exists()

    content = output_file.read_text()
    assert "REQ-001" in content
    assert "Missing success metrics" in content


def test_explain_no_color() -> None:
    """Test explain with --no-color flag."""
    result = runner.invoke(app, ["explain", "REQ-001", "--no-color"])

    assert result.exit_code == 0
    assert "REQ-001" in result.stdout
    # Output should not have ANSI escape codes
    assert "\x1b[" not in result.stdout


def test_explain_all_rules() -> None:
    """Test that all 12 rules can be explained individually."""
    rule_ids = [
        "REQ-001",
        "REQ-002",
        "REQ-003",
        "ARCH-001",
        "ARCH-002",
        "ARCH-003",
        "TEST-001",
        "OPS-001",
        "OPS-002",
        "SEC-001",
        "PERF-001",
        "DOC-001",
    ]

    expected_titles = {
        "REQ-001": "Missing success metrics",
        "REQ-002": "Unclear scope or goals",
        "REQ-003": "Missing non-functional requirements",
        "ARCH-001": "Missing error handling strategy",
        "ARCH-002": "Unclear dependencies",
        "ARCH-003": "Missing data retention/privacy plan",
        "TEST-001": "Missing test strategy",
        "OPS-001": "Missing rollout/deployment plan",
        "OPS-002": "Unclear ownership",
        "SEC-001": "Missing security considerations",
        "PERF-001": "Missing performance targets",
        "DOC-001": "Missing decision rationale",
    }

    for rule_id in rule_ids:
        result = runner.invoke(app, ["explain", rule_id])
        assert result.exit_code == 0, f"Failed to explain {rule_id}"
        assert rule_id in result.stdout
        assert expected_titles[rule_id] in result.stdout


def test_explain_invalid_format() -> None:
    """Test explain with invalid --format option."""
    result = runner.invoke(app, ["explain", "REQ-001", "--format", "xml"])

    assert result.exit_code == 2
    assert "Error" in result.output or "error" in result.output.lower()
    assert "format" in result.output.lower()


def test_explain_list_with_output_file(tmp_path: Path) -> None:
    """Test writing list output to a file."""
    output_file = tmp_path / "rules_list.txt"
    result = runner.invoke(app, ["explain", "--list", "--output", str(output_file)])

    assert result.exit_code == 0
    assert output_file.exists()

    content = output_file.read_text()
    assert "REQ-001" in content
    assert "ARCH-001" in content


def test_explain_json_output_to_file(tmp_path: Path) -> None:
    """Test writing JSON explain output to a file."""
    output_file = tmp_path / "explanation.json"
    result = runner.invoke(
        app, ["explain", "ARCH-001", "--format", "json", "--output", str(output_file)]
    )

    assert result.exit_code == 0
    assert output_file.exists()

    content = output_file.read_text()
    parsed = json.loads(content)
    assert parsed["id"] == "ARCH-001"
    assert parsed["title"] == "Missing error handling strategy"
