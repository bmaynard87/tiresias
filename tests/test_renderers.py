"""Tests for output renderers."""

import json

from tiresias.renderers.json import render_json
from tiresias.renderers.text import render_text
from tiresias.schemas.report import (
    Category,
    Finding,
    Metadata,
    ReviewReport,
    Severity,
)


def test_render_json_valid() -> None:
    """Test that JSON renderer produces valid JSON."""
    report = ReviewReport(
        metadata=Metadata(
            tool_version="0.1.0",
            timestamp="2024-01-01T00:00:00Z",
            input_files=["test.md"],
            profile="general",
            elapsed_ms=100,
        ),
        findings=[],
        assumptions=[],
        open_questions=[],
        quick_summary=["No issues found"],
        risk_score=0,
        risk_score_explanation="Risk score: 0/100 (Low)",
    )

    output = render_json(report)

    # Should be valid JSON
    parsed = json.loads(output)
    assert parsed["metadata"]["tool_version"] == "0.1.0"
    assert parsed["risk_score"] == 0


def test_render_json_deterministic() -> None:
    """Test that JSON output is deterministic."""
    report = ReviewReport(
        metadata=Metadata(
            tool_version="0.1.0",
            timestamp="2024-01-01T00:00:00Z",
            input_files=["test.md"],
            profile="general",
            elapsed_ms=100,
        ),
        findings=[
            Finding(
                id="TEST-001",
                title="Test Finding",
                severity=Severity.HIGH,
                category=Category.REQUIREMENTS,
                evidence="Evidence",
                impact="Impact",
                recommendation="Recommendation",
            ),
        ],
        assumptions=["Assumption 1"],
        open_questions=["Question 1"],
        quick_summary=["Summary"],
        risk_score=15,
        risk_score_explanation="15/100",
    )

    output1 = render_json(report)
    output2 = render_json(report)

    # Should be identical
    assert output1 == output2


def test_render_json_includes_findings() -> None:
    """Test that JSON includes all findings."""
    report = ReviewReport(
        metadata=Metadata(
            tool_version="0.1.0",
            timestamp="2024-01-01T00:00:00Z",
            input_files=["test.md"],
            profile="general",
            elapsed_ms=100,
        ),
        findings=[
            Finding(
                id="TEST-001",
                title="First Finding",
                severity=Severity.HIGH,
                category=Category.REQUIREMENTS,
                evidence="Evidence 1",
                impact="Impact 1",
                recommendation="Recommendation 1",
            ),
            Finding(
                id="TEST-002",
                title="Second Finding",
                severity=Severity.MEDIUM,
                category=Category.TESTING,
                evidence="Evidence 2",
                impact="Impact 2",
                recommendation="Recommendation 2",
            ),
        ],
        assumptions=[],
        open_questions=[],
        quick_summary=["2 findings"],
        risk_score=23,
        risk_score_explanation="23/100",
    )

    output = render_json(report)
    parsed = json.loads(output)

    assert len(parsed["findings"]) == 2
    assert parsed["findings"][0]["id"] == "TEST-001"
    assert parsed["findings"][1]["id"] == "TEST-002"


def test_render_text_includes_sections() -> None:
    """Test that text renderer includes expected sections."""
    report = ReviewReport(
        metadata=Metadata(
            tool_version="0.1.0",
            timestamp="2024-01-01T00:00:00Z",
            input_files=["test.md"],
            profile="general",
            elapsed_ms=100,
        ),
        findings=[
            Finding(
                id="HIGH-001",
                title="High Severity Finding",
                severity=Severity.HIGH,
                category=Category.ARCHITECTURE,
                evidence="Evidence",
                impact="Impact",
                recommendation="Fix this",
            ),
        ],
        assumptions=["Test assumption"],
        open_questions=["Test question?"],
        quick_summary=["1 high finding"],
        risk_score=15,
        risk_score_explanation="Risk score: 15/100 (Low)",
    )

    output = render_text(report, no_color=True)

    # Should include key sections
    assert "Tiresias" in output
    assert "Risk Score" in output
    assert "15/100" in output
    assert "High Severity" in output
    assert "HIGH-001" in output
    assert "Assumptions" in output
    assert "Open Questions" in output
    assert "Summary" in output


def test_render_text_no_color() -> None:
    """Test that no_color flag works."""
    report = ReviewReport(
        metadata=Metadata(
            tool_version="0.1.0",
            timestamp="2024-01-01T00:00:00Z",
            input_files=["test.md"],
            profile="general",
            elapsed_ms=100,
        ),
        findings=[],
        assumptions=[],
        open_questions=[],
        quick_summary=["Clean"],
        risk_score=0,
        risk_score_explanation="0/100 (Low)",
    )

    output = render_text(report, no_color=True)

    # Should not contain ANSI escape codes
    assert "\x1b[" not in output
