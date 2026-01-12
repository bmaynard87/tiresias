"""Tests for suppression engine."""

from datetime import UTC, date, datetime, timedelta

import pytest

from tiresias.core.suppression import apply_suppressions
from tiresias.schemas.config import SuppressionEntry, TiresiasConfig
from tiresias.schemas.report import Category, Finding, Severity


def test_suppression_entry_validates_reason() -> None:
    """Test that empty reason fails validation."""
    with pytest.raises(ValueError, match="reason cannot be empty"):
        SuppressionEntry(id="REQ-001", reason="")

    with pytest.raises(ValueError, match="reason cannot be empty"):
        SuppressionEntry(id="REQ-001", reason="   ")


def test_suppression_entry_validates_expires_format() -> None:
    """Test that invalid expires format fails validation."""
    with pytest.raises(ValueError, match="YYYY-MM-DD format"):
        SuppressionEntry(id="REQ-001", reason="Valid reason", expires="2024/01/01")

    with pytest.raises(ValueError, match="YYYY-MM-DD format"):
        SuppressionEntry(id="REQ-001", reason="Valid reason", expires="01-01-2024")

    with pytest.raises(ValueError, match="YYYY-MM-DD format"):
        SuppressionEntry(id="REQ-001", reason="Valid reason", expires="invalid")


def test_suppression_entry_accepts_valid_expires() -> None:
    """Test that valid expires date is accepted."""
    entry = SuppressionEntry(id="REQ-001", reason="Valid reason", expires="2024-12-31")
    assert entry.expires == "2024-12-31"


def test_suppression_entry_accepts_none_expires() -> None:
    """Test that None expires is accepted."""
    entry = SuppressionEntry(id="REQ-001", reason="Valid reason", expires=None)
    assert entry.expires is None


def test_apply_suppressions_no_suppressions() -> None:
    """Test with no suppressions configured."""
    findings = [
        Finding(
            id="REQ-001",
            title="Test",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        )
    ]
    config = TiresiasConfig()

    result = apply_suppressions(findings, config, "general", ["test.md"])

    assert len(result.visible_findings) == 1
    assert len(result.suppressed_findings) == 0
    assert result.get_suppressed_summary() is None
    assert len(result.expired_suppressions) == 0


def test_apply_suppressions_exact_match() -> None:
    """Test exact rule ID match suppression."""
    findings = [
        Finding(
            id="REQ-001",
            title="Test",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        )
    ]
    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(id="REQ-001", reason="Accepted risk"),
        ]
    )

    result = apply_suppressions(findings, config, "general", ["test.md"])

    assert len(result.visible_findings) == 0
    assert len(result.suppressed_findings) == 1
    assert result.suppressed_findings[0].suppressed is True
    assert result.suppressed_findings[0].suppression is not None
    assert result.suppressed_findings[0].suppression.reason == "Accepted risk"


def test_apply_suppressions_no_match() -> None:
    """Test suppression that doesn't match any findings."""
    findings = [
        Finding(
            id="REQ-001",
            title="Test",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        )
    ]
    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(id="ARCH-001", reason="Different rule"),
        ]
    )

    result = apply_suppressions(findings, config, "general", ["test.md"])

    assert len(result.visible_findings) == 1
    assert len(result.suppressed_findings) == 0


def test_apply_suppressions_profile_filter_match() -> None:
    """Test suppression with profile filter that matches."""
    findings = [
        Finding(
            id="REQ-001",
            title="Test",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        )
    ]
    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(id="REQ-001", reason="Profile match", profiles=["general"]),
        ]
    )

    result = apply_suppressions(findings, config, "general", ["test.md"])

    assert len(result.visible_findings) == 0
    assert len(result.suppressed_findings) == 1


def test_apply_suppressions_profile_filter_no_match() -> None:
    """Test suppression with profile filter that doesn't match."""
    findings = [
        Finding(
            id="REQ-001",
            title="Test",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        )
    ]
    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(id="REQ-001", reason="Wrong profile", profiles=["security"]),
        ]
    )

    result = apply_suppressions(findings, config, "general", ["test.md"])

    assert len(result.visible_findings) == 1
    assert len(result.suppressed_findings) == 0


def test_apply_suppressions_severity_filter_match() -> None:
    """Test suppression with severity filter that matches."""
    findings = [
        Finding(
            id="REQ-001",
            title="Test",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        )
    ]
    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(id="REQ-001", reason="Severity match", severities=["high"]),
        ]
    )

    result = apply_suppressions(findings, config, "general", ["test.md"])

    assert len(result.visible_findings) == 0
    assert len(result.suppressed_findings) == 1


def test_apply_suppressions_severity_filter_no_match() -> None:
    """Test suppression with severity filter that doesn't match."""
    findings = [
        Finding(
            id="REQ-001",
            title="Test",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        )
    ]
    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(id="REQ-001", reason="Wrong severity", severities=["low"]),
        ]
    )

    result = apply_suppressions(findings, config, "general", ["test.md"])

    assert len(result.visible_findings) == 1
    assert len(result.suppressed_findings) == 0


def test_apply_suppressions_scope_filter_match() -> None:
    """Test suppression with scope filter that matches."""
    findings = [
        Finding(
            id="REQ-001",
            title="Test",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        )
    ]
    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(id="REQ-001", reason="Scope match", scope=["*.md"]),
        ]
    )

    result = apply_suppressions(findings, config, "general", ["test.md"])

    assert len(result.visible_findings) == 0
    assert len(result.suppressed_findings) == 1


def test_apply_suppressions_scope_filter_no_match() -> None:
    """Test suppression with scope filter that doesn't match."""
    findings = [
        Finding(
            id="REQ-001",
            title="Test",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        )
    ]
    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(id="REQ-001", reason="Wrong scope", scope=["*.txt"]),
        ]
    )

    result = apply_suppressions(findings, config, "general", ["test.md"])

    assert len(result.visible_findings) == 1
    assert len(result.suppressed_findings) == 0


def test_apply_suppressions_scope_glob_patterns() -> None:
    """Test various glob patterns in scope."""
    findings = [
        Finding(
            id="REQ-001",
            title="Test",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        )
    ]

    # Test ** wildcard
    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(id="REQ-001", reason="Deep match", scope=["docs/**/*.md"]),
        ]
    )
    result = apply_suppressions(findings, config, "general", ["docs/design/spec.md"])
    assert len(result.suppressed_findings) == 1

    # Test directory match
    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(id="REQ-001", reason="Dir match", scope=["docs/*"]),
        ]
    )
    result = apply_suppressions(findings, config, "general", ["docs/spec.md"])
    assert len(result.suppressed_findings) == 1


def test_apply_suppressions_expired() -> None:
    """Test that expired suppressions don't suppress but generate warnings."""
    findings = [
        Finding(
            id="REQ-001",
            title="Test",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        )
    ]

    yesterday = (datetime.now(UTC).date() - timedelta(days=1)).isoformat()

    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(id="REQ-001", reason="Expired", expires=yesterday),
        ]
    )

    result = apply_suppressions(findings, config, "general", ["test.md"])

    # Finding NOT suppressed
    assert len(result.visible_findings) == 1
    assert len(result.suppressed_findings) == 0

    # But expiry recorded
    assert len(result.expired_suppressions) == 1
    assert result.expired_suppressions[0].id == "REQ-001"
    assert result.expired_suppressions[0].expires == yesterday


def test_apply_suppressions_not_expired() -> None:
    """Test that future expiry still suppresses."""
    findings = [
        Finding(
            id="REQ-001",
            title="Test",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        )
    ]

    tomorrow = (datetime.now(UTC).date() + timedelta(days=1)).isoformat()

    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(id="REQ-001", reason="Still valid", expires=tomorrow),
        ]
    )

    result = apply_suppressions(findings, config, "general", ["test.md"])

    assert len(result.visible_findings) == 0
    assert len(result.suppressed_findings) == 1
    assert len(result.expired_suppressions) == 0


def test_apply_suppressions_today_expires() -> None:
    """Test that expires=today still suppresses (expires at end of day)."""
    findings = [
        Finding(
            id="REQ-001",
            title="Test",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        )
    ]

    today = date.today().isoformat()

    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(id="REQ-001", reason="Expires today", expires=today),
        ]
    )

    result = apply_suppressions(findings, config, "general", ["test.md"])

    # Still suppresses (expires at end of day)
    assert len(result.visible_findings) == 0
    assert len(result.suppressed_findings) == 1


def test_apply_suppressions_multiple_findings() -> None:
    """Test with multiple findings, some suppressed."""
    findings = [
        Finding(
            id="REQ-001",
            title="Test1",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        ),
        Finding(
            id="ARCH-001",
            title="Test2",
            severity=Severity.MEDIUM,
            category=Category.ARCHITECTURE,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        ),
        Finding(
            id="REQ-002",
            title="Test3",
            severity=Severity.LOW,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        ),
    ]

    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(id="REQ-001", reason="Suppressed"),
            SuppressionEntry(id="REQ-002", reason="Also suppressed"),
        ]
    )

    result = apply_suppressions(findings, config, "general", ["test.md"])

    assert len(result.visible_findings) == 1
    assert result.visible_findings[0].id == "ARCH-001"
    assert len(result.suppressed_findings) == 2


def test_suppressed_summary_counts_by_severity() -> None:
    """Test that suppressed summary correctly counts by severity."""
    findings = [
        Finding(
            id="REQ-001",
            title="High1",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        ),
        Finding(
            id="REQ-002",
            title="High2",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        ),
        Finding(
            id="ARCH-001",
            title="Medium",
            severity=Severity.MEDIUM,
            category=Category.ARCHITECTURE,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        ),
        Finding(
            id="DOC-001",
            title="Low",
            severity=Severity.LOW,
            category=Category.DOCUMENTATION,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        ),
    ]

    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(id="REQ-001", reason="Suppressed"),
            SuppressionEntry(id="REQ-002", reason="Suppressed"),
            SuppressionEntry(id="ARCH-001", reason="Suppressed"),
            SuppressionEntry(id="DOC-001", reason="Suppressed"),
        ]
    )

    result = apply_suppressions(findings, config, "general", ["test.md"])
    summary = result.get_suppressed_summary()

    assert summary is not None
    assert summary.total == 4
    assert summary.by_severity["high"] == 2
    assert summary.by_severity["medium"] == 1
    assert summary.by_severity["low"] == 1


def test_suppression_first_match_wins() -> None:
    """Test that first matching suppression is used."""
    findings = [
        Finding(
            id="REQ-001",
            title="Test",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        )
    ]

    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(id="REQ-001", reason="First reason", expires="2030-01-01"),
            SuppressionEntry(id="REQ-001", reason="Second reason", expires="2030-12-31"),
        ]
    )

    result = apply_suppressions(findings, config, "general", ["test.md"])

    assert len(result.suppressed_findings) == 1
    assert result.suppressed_findings[0].suppression.reason == "First reason"
    assert result.suppressed_findings[0].suppression.expires == "2030-01-01"


def test_suppression_combined_filters() -> None:
    """Test suppression with multiple filters combined."""
    findings = [
        Finding(
            id="REQ-001",
            title="Test",
            severity=Severity.HIGH,
            category=Category.REQUIREMENTS,
            evidence="test",
            impact="test impact",
            recommendation="fix",
        )
    ]

    # All filters match
    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(
                id="REQ-001",
                reason="All match",
                profiles=["general"],
                severities=["high"],
                scope=["*.md"],
            ),
        ]
    )
    result = apply_suppressions(findings, config, "general", ["test.md"])
    assert len(result.suppressed_findings) == 1

    # One filter doesn't match (profile)
    config = TiresiasConfig(
        suppressions=[
            SuppressionEntry(
                id="REQ-001",
                reason="Profile mismatch",
                profiles=["security"],
                severities=["high"],
                scope=["*.md"],
            ),
        ]
    )
    result = apply_suppressions(findings, config, "general", ["test.md"])
    assert len(result.suppressed_findings) == 0
