"""Tests for the heuristic analyzer."""

import pytest

from tiresias.core.analyzer import HeuristicAnalyzer
from tiresias.schemas.report import Severity


def test_analyzer_req001_fires_without_metrics() -> None:
    """Test REQ-001 fires when success metrics are missing."""
    analyzer = HeuristicAnalyzer()
    content = "# Design\nSome project description without metrics."

    findings = analyzer.analyze(content, "general")
    req001 = [f for f in findings if f.id == "REQ-001"]

    assert len(req001) == 1
    assert req001[0].severity == Severity.HIGH
    assert "success" in req001[0].title.lower()


def test_analyzer_req001_not_fires_with_metrics() -> None:
    """Test REQ-001 doesn't fire when success metrics are present."""
    analyzer = HeuristicAnalyzer()
    content = """
    # Design
    ## Success Criteria
    We will measure success by 80% user adoption.
    """

    findings = analyzer.analyze(content, "general")
    req001 = [f for f in findings if f.id == "REQ-001"]

    assert len(req001) == 0


def test_analyzer_arch001_fires_without_error_handling() -> None:
    """Test ARCH-001 fires when error handling is missing."""
    analyzer = HeuristicAnalyzer()
    content = """
    # Payment Service
    ## Architecture
    We will use REST API with PostgreSQL.
    """

    findings = analyzer.analyze(content, "general")
    arch001 = [f for f in findings if f.id == "ARCH-001"]

    assert len(arch001) == 1
    assert arch001[0].severity == Severity.HIGH


def test_analyzer_arch001_not_fires_with_error_handling() -> None:
    """Test ARCH-001 doesn't fire when error handling is discussed."""
    analyzer = HeuristicAnalyzer()
    content = """
    # Design
    ## Error Handling
    We will handle errors gracefully with retry logic and fallbacks.
    """

    findings = analyzer.analyze(content, "general")
    arch001 = [f for f in findings if f.id == "ARCH-001"]

    assert len(arch001) == 0


def test_analyzer_profile_general_includes_all_rules() -> None:
    """Test general profile includes all rules."""
    analyzer = HeuristicAnalyzer()
    content = "# Minimal doc"

    findings = analyzer.analyze(content, "general")

    # Should have many findings (12 rules)
    assert len(findings) >= 10


def test_analyzer_profile_security_filters() -> None:
    """Test security profile filters to relevant rules."""
    analyzer = HeuristicAnalyzer()
    content = "# Minimal doc"

    general_findings = analyzer.analyze(content, "general")
    security_findings = analyzer.analyze(content, "security")

    # Security profile should have fewer findings
    assert len(security_findings) < len(general_findings)

    # Security findings should only have specific IDs
    security_ids = {f.id for f in security_findings}
    assert all(
        f_id.startswith(("REQ-", "SEC-", "OPS-002")) or f_id == "ARCH-003"
        for f_id in security_ids
    )


def test_extract_assumptions() -> None:
    """Test assumption extraction."""
    analyzer = HeuristicAnalyzer()
    content = """
    # Design

    We assume that the API will support 1000 requests per second.
    Given that users authenticate via OAuth, we don't need password storage.
    Assuming the database is replicated for high availability.
    """

    assumptions = analyzer.extract_assumptions(content)

    assert len(assumptions) >= 2
    assert any("api" in a.lower() for a in assumptions)
    assert any("oauth" in a.lower() or "users" in a.lower() for a in assumptions)


def test_extract_questions() -> None:
    """Test open question extraction."""
    analyzer = HeuristicAnalyzer()
    content = """
    # Design

    What should we do about rate limiting?
    How do we handle offline scenarios?

    TODO: Decide on caching strategy
    TBD: Choose between MySQL and PostgreSQL
    """

    questions = analyzer.extract_questions(content)

    assert len(questions) >= 2
    # Should capture questions with ?
    assert any("?" in q for q in questions)
    # Should capture TODO/TBD
    assert any("TODO" in q or "TBD" in q for q in questions)


def test_findings_are_sorted() -> None:
    """Test that findings are sorted deterministically."""
    analyzer = HeuristicAnalyzer()
    content = "# Minimal doc"

    findings = analyzer.analyze(content, "general")

    # Check severity order (high -> medium -> low)
    severities = [f.severity for f in findings]
    high_indices = [i for i, s in enumerate(severities) if s == Severity.HIGH]
    med_indices = [i for i, s in enumerate(severities) if s == Severity.MEDIUM]
    low_indices = [i for i, s in enumerate(severities) if s == Severity.LOW]

    if high_indices and med_indices:
        assert max(high_indices) < min(med_indices)
    if med_indices and low_indices:
        assert max(med_indices) < min(low_indices)
