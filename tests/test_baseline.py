"""Tests for baseline comparison logic."""

from tiresias.core.baseline import FindingKey, check_maturity_regression, compare_findings
from tiresias.schemas.report import Category, Finding, Severity


def test_finding_key_equality() -> None:
    """Test FindingKey comparison."""
    key1 = FindingKey(rule_id="REQ-001", category="requirements")
    key2 = FindingKey(rule_id="REQ-001", category="requirements")
    key3 = FindingKey(rule_id="REQ-002", category="requirements")

    assert key1 == key2
    assert key1 != key3
    assert hash(key1) == hash(key2)


def test_finding_key_from_finding() -> None:
    """Test creating FindingKey from Finding."""
    finding = Finding(
        id="REQ-001",
        title="Test finding",
        severity=Severity.HIGH,
        category=Category.REQUIREMENTS,
        evidence="Test evidence",
        impact="Test impact",
        recommendation="Test recommendation",
    )

    key = FindingKey.from_finding(finding)

    assert key.rule_id == "REQ-001"
    assert key.category == "requirements"


def test_compare_findings_new() -> None:
    """Test detection of new findings."""
    baseline: list[Finding] = []
    current = [
        Finding(
            id="REQ-001",
            title="Missing success metrics",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="No metrics section",
            impact="Hard to measure success",
            recommendation="Add metrics",
        )
    ]

    new, worsened, unchanged, improved = compare_findings(current, baseline)

    assert len(new) == 1
    assert len(worsened) == 0
    assert len(unchanged) == 0
    assert len(improved) == 0
    assert new[0].id == "REQ-001"


def test_compare_findings_worsened() -> None:
    """Test detection of worsened findings."""
    baseline = [
        Finding(
            id="REQ-001",
            title="Missing success metrics",
            severity=Severity.LOW,
            category=Category.REQUIREMENTS,
            evidence="No metrics section",
            impact="Hard to measure success",
            recommendation="Add metrics",
        )
    ]
    current = [
        Finding(
            id="REQ-001",
            title="Missing success metrics",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="No metrics section",
            impact="Hard to measure success",
            recommendation="Add metrics",
        )
    ]

    new, worsened, unchanged, improved = compare_findings(current, baseline)

    assert len(new) == 0
    assert len(worsened) == 1
    assert len(unchanged) == 0
    assert len(improved) == 0
    assert worsened[0][0].id == "REQ-001"
    assert worsened[0][0].severity == Severity.HIGH
    assert worsened[0][1] == Severity.LOW  # baseline severity


def test_compare_findings_unchanged() -> None:
    """Test detection of unchanged findings."""
    baseline = [
        Finding(
            id="REQ-001",
            title="Missing success metrics",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="No metrics section",
            impact="Hard to measure success",
            recommendation="Add metrics",
        )
    ]
    current = [
        Finding(
            id="REQ-001",
            title="Missing success metrics",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="No metrics section",
            impact="Hard to measure success",
            recommendation="Add metrics",
        )
    ]

    new, worsened, unchanged, improved = compare_findings(current, baseline)

    assert len(new) == 0
    assert len(worsened) == 0
    assert len(unchanged) == 1
    assert len(improved) == 0
    assert unchanged[0].id == "REQ-001"


def test_compare_findings_improved() -> None:
    """Test detection of improved findings."""
    baseline = [
        Finding(
            id="REQ-001",
            title="Missing success metrics",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="No metrics section",
            impact="Hard to measure success",
            recommendation="Add metrics",
        )
    ]
    current = [
        Finding(
            id="REQ-001",
            title="Missing success metrics",
            severity=Severity.LOW,
            category=Category.REQUIREMENTS,
            evidence="No metrics section",
            impact="Hard to measure success",
            recommendation="Add metrics",
        )
    ]

    new, worsened, unchanged, improved = compare_findings(current, baseline)

    assert len(new) == 0
    assert len(worsened) == 0
    assert len(unchanged) == 0
    assert len(improved) == 1
    assert improved[0][0].id == "REQ-001"
    assert improved[0][0].severity == Severity.LOW
    assert improved[0][1] == Severity.HIGH  # baseline severity


def test_compare_findings_multiple_changes() -> None:
    """Test comparison with multiple finding changes."""
    baseline = [
        Finding(
            id="REQ-001",
            title="Finding 1",
            severity=Severity.LOW,
            category=Category.REQUIREMENTS,
            evidence="Evidence 1",
            impact="Impact 1",
            recommendation="Recommendation 1",
        ),
        Finding(
            id="ARCH-001",
            title="Finding 2",
            severity=Severity.HIGH,
            category=Category.ARCHITECTURE,
            evidence="Evidence 2",
            impact="Impact 2",
            recommendation="Recommendation 2",
        ),
        Finding(
            id="TEST-001",
            title="Finding 3",
            severity=Severity.MEDIUM,
            category=Category.TESTING,
            evidence="Evidence 3",
            impact="Impact 3",
            recommendation="Recommendation 3",
        ),
    ]
    current = [
        Finding(
            id="REQ-001",
            title="Finding 1",
            severity=Severity.HIGH,  # Worsened
            category=Category.REQUIREMENTS,
            evidence="Evidence 1",
            impact="Impact 1",
            recommendation="Recommendation 1",
        ),
        Finding(
            id="ARCH-001",
            title="Finding 2",
            severity=Severity.HIGH,  # Unchanged
            category=Category.ARCHITECTURE,
            evidence="Evidence 2",
            impact="Impact 2",
            recommendation="Recommendation 2",
        ),
        Finding(
            id="TEST-001",
            title="Finding 3",
            severity=Severity.LOW,  # Improved
            category=Category.TESTING,
            evidence="Evidence 3",
            impact="Impact 3",
            recommendation="Recommendation 3",
        ),
        Finding(
            id="SEC-001",
            title="Finding 4",
            severity=Severity.MEDIUM,  # New
            category=Category.SECURITY,
            evidence="Evidence 4",
            impact="Impact 4",
            recommendation="Recommendation 4",
        ),
    ]

    new, worsened, unchanged, improved = compare_findings(current, baseline)

    assert len(new) == 1
    assert len(worsened) == 1
    assert len(unchanged) == 1
    assert len(improved) == 1

    assert new[0].id == "SEC-001"
    assert worsened[0][0].id == "REQ-001"
    assert unchanged[0].id == "ARCH-001"
    assert improved[0][0].id == "TEST-001"


def test_check_maturity_regression() -> None:
    """Test maturity regression detection."""
    assert check_maturity_regression(30, 50) is True  # Decreased
    assert check_maturity_regression(50, 30) is False  # Increased
    assert check_maturity_regression(50, 50) is False  # Same
    assert check_maturity_regression(0, 100) is True  # Large decrease
    assert check_maturity_regression(100, 0) is False  # Large increase
