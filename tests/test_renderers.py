"""Tests for output renderers."""

import json

from tiresias import __version__
from tiresias.renderers.json import render_json
from tiresias.renderers.text import render_text
from tiresias.schemas.report import (
    Category,
    Finding,
    Maturity,
    MaturityMetrics,
    Metadata,
    ReviewReport,
    Severity,
)


def _create_test_maturity() -> Maturity:
    """Create a default maturity object for tests."""
    return Maturity(
        level="early_draft",
        score=30,
        confidence="medium",
        interpretation="Test maturity",
        signals=["test_signal"],
        metrics=MaturityMetrics(
            char_count=100,
            section_count=2,
            core_sections_present=1,
            core_sections_found=["goals_scope"],
        ),
    )


def test_render_json_valid() -> None:
    """Test that JSON renderer produces valid JSON."""
    report = ReviewReport(
        metadata=Metadata(
            tool_version=__version__,
            timestamp="2024-01-01T00:00:00Z",
            input_files=["test.md"],
            profile="general",
            elapsed_ms=100,
        ),
        maturity=_create_test_maturity(),
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
    assert parsed["metadata"]["tool_version"] == __version__
    assert isinstance(parsed["metadata"]["tool_version"], str)
    assert len(parsed["metadata"]["tool_version"]) > 0
    assert parsed["risk_score"] == 0


def test_render_json_deterministic() -> None:
    """Test that JSON output is deterministic."""
    report = ReviewReport(
        metadata=Metadata(
            tool_version=__version__,
            timestamp="2024-01-01T00:00:00Z",
            input_files=["test.md"],
            profile="general",
            elapsed_ms=100,
        ),
        maturity=_create_test_maturity(),
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
            tool_version=__version__,
            timestamp="2024-01-01T00:00:00Z",
            input_files=["test.md"],
            profile="general",
            elapsed_ms=100,
        ),
        maturity=_create_test_maturity(),
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
            tool_version=__version__,
            timestamp="2024-01-01T00:00:00Z",
            input_files=["test.md"],
            profile="general",
            elapsed_ms=100,
        ),
        maturity=_create_test_maturity(),
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
            tool_version=__version__,
            timestamp="2024-01-01T00:00:00Z",
            input_files=["test.md"],
            profile="general",
            elapsed_ms=100,
        ),
        maturity=_create_test_maturity(),
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


def test_render_text_evidence_truncation_high_severity() -> None:
    """Test that high severity shows full evidence."""
    report = ReviewReport(
        metadata=Metadata(
            tool_version=__version__,
            timestamp="2024-01-01T00:00:00Z",
            input_files=["test.md"],
            profile="general",
            elapsed_ms=100,
        ),
        maturity=_create_test_maturity(),
        findings=[
            Finding(
                id="HIGH-001",
                title="High Finding",
                severity=Severity.HIGH,
                category=Category.ARCHITECTURE,
                evidence="First sentence. Second sentence. Third sentence. Fourth sentence.",
                impact="Impact",
                recommendation="Fix",
            ),
        ],
        assumptions=[],
        open_questions=[],
        quick_summary=["1 finding"],
        risk_score=15,
        risk_score_explanation="15/100",
    )

    output = render_text(report, no_color=True, show_evidence=True)

    # High severity should show all sentences
    assert "First sentence" in output
    assert "Fourth sentence" in output
    assert "..." not in output or "Fourth sentence..." not in output  # No truncation on last


def test_render_text_evidence_truncation_medium_severity() -> None:
    """Test that medium severity truncates to 2 sentences."""
    report = ReviewReport(
        metadata=Metadata(
            tool_version=__version__,
            timestamp="2024-01-01T00:00:00Z",
            input_files=["test.md"],
            profile="general",
            elapsed_ms=100,
        ),
        maturity=_create_test_maturity(),
        findings=[
            Finding(
                id="MED-001",
                title="Medium Finding",
                severity=Severity.MEDIUM,
                category=Category.TESTING,
                evidence="First sentence. Second sentence. Third sentence. Fourth sentence.",
                impact="Impact",
                recommendation="Fix",
            ),
        ],
        assumptions=[],
        open_questions=[],
        quick_summary=["1 finding"],
        risk_score=8,
        risk_score_explanation="8/100",
    )

    output = render_text(report, no_color=True, show_evidence=True)

    # Medium should show first 2 sentences and add ellipsis
    assert "First sentence" in output
    assert "Second sentence" in output
    assert "..." in output


def test_render_text_evidence_truncation_low_severity() -> None:
    """Test that low severity truncates to 1 sentence."""
    report = ReviewReport(
        metadata=Metadata(
            tool_version=__version__,
            timestamp="2024-01-01T00:00:00Z",
            input_files=["test.md"],
            profile="general",
            elapsed_ms=100,
        ),
        maturity=_create_test_maturity(),
        findings=[
            Finding(
                id="LOW-001",
                title="Low Finding",
                severity=Severity.LOW,
                category=Category.DOCUMENTATION,
                evidence="First sentence. Second sentence. Third sentence.",
                impact="Impact",
                recommendation="Fix",
            ),
        ],
        assumptions=[],
        open_questions=[],
        quick_summary=["1 finding"],
        risk_score=3,
        risk_score_explanation="3/100",
    )

    output = render_text(report, no_color=True, show_evidence=True)

    # Low should show only first sentence with ellipsis
    assert "First sentence" in output
    assert "..." in output


def test_render_json_always_includes_evidence() -> None:
    """Test that JSON always includes evidence regardless of flag."""
    report = ReviewReport(
        metadata=Metadata(
            tool_version=__version__,
            timestamp="2024-01-01T00:00:00Z",
            input_files=["test.md"],
            profile="general",
            elapsed_ms=100,
        ),
        maturity=_create_test_maturity(),
        findings=[
            Finding(
                id="TEST-001",
                title="Test",
                severity=Severity.HIGH,
                category=Category.REQUIREMENTS,
                evidence="Test evidence",
                impact="Impact",
                recommendation="Fix",
            ),
        ],
        assumptions=[],
        open_questions=[],
        quick_summary=["1 finding"],
        risk_score=15,
        risk_score_explanation="15/100",
    )

    output = render_json(report)
    parsed = json.loads(output)

    # JSON should always include evidence
    assert parsed["findings"][0]["evidence"] == "Test evidence"


def test_render_text_includes_maturity() -> None:
    """Test that text renderer displays maturity."""
    report = ReviewReport(
        metadata=Metadata(
            tool_version=__version__,
            timestamp="2024-01-01T00:00:00Z",
            input_files=["test.md"],
            profile="general",
            elapsed_ms=100,
        ),
        maturity=Maturity(
            level="early_draft",
            score=35,
            confidence="medium",
            interpretation="Incomplete sections are expected.",
            signals=["short_length", "few_sections"],
            metrics=MaturityMetrics(
                char_count=800,
                section_count=3,
                core_sections_present=2,
                core_sections_found=["goals_scope", "dependencies"],
            ),
        ),
        findings=[],
        assumptions=[],
        open_questions=[],
        quick_summary=["1 finding"],
        risk_score=15,
        risk_score_explanation="15/100",
    )

    output = render_text(report, no_color=True)

    assert "Document Maturity" in output
    assert "Early Draft" in output
    assert "35/100" in output
    assert "Incomplete sections are expected" in output


def test_render_json_includes_maturity() -> None:
    """Test that JSON includes maturity field."""
    report = ReviewReport(
        metadata=Metadata(
            tool_version=__version__,
            timestamp="2024-01-01T00:00:00Z",
            input_files=["test.md"],
            profile="general",
            elapsed_ms=100,
        ),
        maturity=Maturity(
            level="design_spec",
            score=62,
            confidence="high",
            interpretation="Document is substantial.",
            signals=["comprehensive_length", "many_sections"],
            metrics=MaturityMetrics(
                char_count=3000,
                section_count=8,
                core_sections_present=5,
                core_sections_found=[
                    "goals_scope",
                    "testing",
                    "security",
                    "dependencies",
                    "rollout",
                ],
            ),
        ),
        findings=[],
        assumptions=[],
        open_questions=[],
        quick_summary=["Clean"],
        risk_score=20,
        risk_score_explanation="20/100",
    )

    output = render_json(report)
    parsed = json.loads(output)

    assert "maturity" in parsed
    assert parsed["maturity"]["level"] == "design_spec"
    assert parsed["maturity"]["score"] == 62
    assert len(parsed["maturity"]["signals"]) > 0
    assert "metrics" in parsed["maturity"]
    assert parsed["maturity"]["metrics"]["char_count"] == 3000
