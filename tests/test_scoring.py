"""Tests for risk scoring calculation."""

from tiresias.core.scoring import calculate_risk_score
from tiresias.schemas.report import Category, Finding, Severity


def test_calculate_risk_score_empty() -> None:
    """Test risk score with no findings."""
    score, explanation = calculate_risk_score([], {})

    assert score == 0
    assert "0/100" in explanation


def test_calculate_risk_score_high_severity() -> None:
    """Test risk score with high severity findings."""
    findings = [
        Finding(
            id="TEST-001",
            title="Test Finding",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="Test evidence",
            impact="Test impact",
            recommendation="Test recommendation",
        ),
    ]
    weights = {"requirements": 1.0}

    score, explanation = calculate_risk_score(findings, weights)

    # High = 15 points
    assert score == 15
    assert "15/100" in explanation
    assert "high-severity" in explanation.lower()


def test_calculate_risk_score_multiple_severities() -> None:
    """Test risk score with multiple severity levels."""
    findings = [
        Finding(
            id="TEST-001",
            title="High Finding",
            severity=Severity.HIGH,
            category=Category.SECURITY,
            evidence="Evidence",
            impact="Impact",
            recommendation="Recommendation",
        ),
        Finding(
            id="TEST-002",
            title="Medium Finding",
            severity=Severity.MEDIUM,
            category=Category.TESTING,
            evidence="Evidence",
            impact="Impact",
            recommendation="Recommendation",
        ),
        Finding(
            id="TEST-003",
            title="Low Finding",
            severity=Severity.LOW,
            category=Category.DOCUMENTATION,
            evidence="Evidence",
            impact="Impact",
            recommendation="Recommendation",
        ),
    ]
    weights = {
        "security": 1.0,
        "testing": 1.0,
        "documentation": 1.0,
    }

    score, explanation = calculate_risk_score(findings, weights)

    # High (15) + Medium (8) + Low (3) = 26
    assert score == 26


def test_calculate_risk_score_with_category_weights() -> None:
    """Test that category weights affect score."""
    finding = Finding(
        id="SEC-001",
        title="Security Issue",
        severity=Severity.HIGH,
        category=Category.SECURITY,
        evidence="Evidence",
        impact="Impact",
        recommendation="Recommendation",
    )

    # Without weight
    score_no_weight, _ = calculate_risk_score([finding], {"security": 1.0})
    assert score_no_weight == 15

    # With 1.5x weight
    score_with_weight, _ = calculate_risk_score([finding], {"security": 1.5})
    assert score_with_weight == 22  # 15 * 1.5 = 22.5 -> 22


def test_calculate_risk_score_capped_at_100() -> None:
    """Test that risk score is capped at 100."""
    # Create many high severity findings
    findings = [
        Finding(
            id=f"TEST-{i:03d}",
            title=f"Finding {i}",
            severity=Severity.HIGH,
            category=Category.SECURITY,
            evidence="Evidence",
            impact="Impact",
            recommendation="Recommendation",
        )
        for i in range(20)
    ]
    weights = {"security": 1.5}

    score, _ = calculate_risk_score(findings, weights)

    assert score == 100  # Should be capped


def test_risk_score_explanation_includes_top_issues() -> None:
    """Test that explanation includes top issues."""
    findings = [
        Finding(
            id="HIGH-001",
            title="Missing error handling",
            severity=Severity.HIGH,
            category=Category.ARCHITECTURE,
            evidence="Evidence",
            impact="Impact",
            recommendation="Recommendation",
        ),
        Finding(
            id="HIGH-002",
            title="No security review",
            severity=Severity.HIGH,
            category=Category.SECURITY,
            evidence="Evidence",
            impact="Impact",
            recommendation="Recommendation",
        ),
    ]
    weights = {"architecture": 1.0, "security": 1.0}

    _, explanation = calculate_risk_score(findings, weights)

    assert "Missing error handling" in explanation
    assert "Primary risks:" in explanation


def test_risk_bands() -> None:
    """Test risk band classification."""
    # Low risk (0-20)
    low_findings = [
        Finding(
            id="TEST-001",
            title="Low Issue",
            severity=Severity.LOW,
            category=Category.DOCUMENTATION,
            evidence="E",
            impact="I",
            recommendation="R",
        )
    ]
    score, explanation = calculate_risk_score(low_findings, {"documentation": 1.0})
    assert score <= 20
    assert "Low" in explanation

    # Medium risk (21-50)
    med_findings = [
        Finding(
            id="TEST-001",
            title="Medium Issue",
            severity=Severity.MEDIUM,
            category=Category.TESTING,
            evidence="E",
            impact="I",
            recommendation="R",
        )
        for _ in range(3)
    ]
    score, explanation = calculate_risk_score(med_findings, {"testing": 1.0})
    assert 21 <= score <= 50
    assert "Medium" in explanation

    # High risk (51-80)
    high_findings = [
        Finding(
            id=f"TEST-{i}",
            title="High Issue",
            severity=Severity.HIGH,
            category=Category.SECURITY,
            evidence="E",
            impact="I",
            recommendation="R",
        )
        for i in range(4)
    ]
    score, explanation = calculate_risk_score(high_findings, {"security": 1.0})
    assert 51 <= score <= 80
    assert "High" in explanation
