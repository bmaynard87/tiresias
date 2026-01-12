"""Tests for document maturity computation."""

from tiresias.core.maturity import (
    MaturityMetrics,
    _calculate_confidence,
    _calculate_score,
    _detect_core_sections,
    _determine_level,
    _generate_signals,
    _get_interpretation,
    compute_maturity,
)


def test_maturity_notes_level() -> None:
    """Test notes-level document (very short, no sections)."""
    content = "# Idea\nJust a quick thought about feature X."
    sections = ["idea", "just a quick thought about feature x."]

    result = compute_maturity(content, sections)

    assert result.level == "notes"
    assert result.score < 25
    assert "very_short_length" in result.signals
    assert result.metrics.char_count == len(content)
    assert result.metrics.section_count == len(sections)


def test_maturity_early_draft_level() -> None:
    """Test early draft document (short, few sections)."""
    content = """
# Feature Design

## Goals
Build a new dashboard for analytics that provides real-time insights into user behavior,
system performance, and business metrics. The dashboard should be intuitive, fast, and
accessible to non-technical stakeholders.

## Scope
Focus on admin users only for the initial release. We will include basic analytics
for user activity, system health monitoring, and key business KPIs. Advanced features
like custom dashboards and data exports will be deferred to future iterations.

## Background
This addresses the need identified in Q3 planning sessions where stakeholders
highlighted the lack of visibility into system operations and user engagement metrics.
"""
    sections = ["feature design", "goals", "build a new dashboard for analytics", "scope"]

    result = compute_maturity(content, sections)

    assert result.level == "early_draft"
    assert 25 <= result.score < 50
    assert result.metrics.core_sections_present >= 1
    assert "goals_scope" in result.metrics.core_sections_found


def test_maturity_design_spec_level() -> None:
    """Test design spec document (medium length, many sections)."""
    content = """
# Feature: Analytics Dashboard

## Goals and Objectives
Build a comprehensive analytics dashboard for tracking key metrics.

## Success Metrics
- 80% user adoption within 3 months
- P95 latency under 200ms

## Architecture
React frontend with Node.js backend and PostgreSQL database.

## Dependencies
- PostgreSQL 14
- Redis for session storage
- Auth0 for authentication

## Performance Requirements
Handle 1000 concurrent users with sub-200ms response times.

## Testing Strategy
Unit tests with Jest, E2E tests with Playwright, target 80% coverage.

## Security Considerations
OAuth 2.0, encrypted data at rest, regular security audits.

## Implementation Timeline
Phase 1: Core dashboard (2 weeks)
Phase 2: Advanced features (3 weeks)
"""
    sections = [
        "feature: analytics dashboard",
        "goals and objectives",
        "success metrics",
        "architecture",
        "dependencies",
        "performance requirements",
        "testing strategy",
        "security considerations",
        "implementation timeline",
    ]

    result = compute_maturity(content, sections)

    assert result.level in ("design_spec", "production_ready")
    assert result.score >= 50
    assert result.metrics.core_sections_present >= 4
    assert "goals_scope" in result.metrics.core_sections_found
    assert "success_metrics" in result.metrics.core_sections_found


def test_maturity_production_ready_level() -> None:
    """Test production-ready document (comprehensive)."""
    content = """
# Feature: Advanced Analytics Dashboard

## Goals and Objectives
Build a comprehensive analytics dashboard with real-time data visualization,
customizable widgets, and advanced filtering capabilities.

## Success Metrics
- 80% user adoption within 3 months
- P95 latency < 200ms
- 4.5+ user satisfaction score

## Non-Functional Requirements
- Handle 10,000 concurrent users
- 99.9% uptime SLA
- Sub-200ms P95 latency

## Architecture
Microservices architecture with event-driven design. React frontend,
Node.js backend services, PostgreSQL for data persistence, Redis for
caching, and Kafka for event streaming.

## Dependencies
- PostgreSQL 15
- Redis 7.x for caching
- Kafka for event streaming
- Auth0 for authentication
- DataDog for monitoring

## Error Handling
Circuit breakers for external services, retry logic with exponential
backoff, graceful degradation for non-critical features.

## Testing Strategy
Unit tests (>80% coverage), integration tests, E2E tests with Playwright,
performance testing with k6, security testing with OWASP ZAP.

## Rollout Plan
Phased rollout: 10% → 25% → 50% → 100% over 2 weeks.
Feature flags for quick rollback. Monitoring with DataDog.

## Security Considerations
OAuth 2.0 authentication, encrypted data at rest and in transit,
regular security audits, data retention policies.

## Ownership
Team: Platform Engineering
Primary Contact: @platform-lead
On-call: @platform-oncall
"""
    sections = [
        "feature: advanced analytics dashboard",
        "goals and objectives",
        "success metrics",
        "non-functional requirements",
        "architecture",
        "dependencies",
        "error handling",
        "testing strategy",
        "rollout plan",
        "security considerations",
        "ownership",
    ]

    result = compute_maturity(content, sections)

    assert result.level == "production_ready"
    assert result.score >= 75
    assert result.metrics.core_sections_present >= 7
    assert "comprehensive_coverage" in result.signals


def test_maturity_core_section_detection() -> None:
    """Test detection of all 9 core sections."""
    sections = [
        "goals and objectives",
        "success metrics and kpis",
        "performance and scalability requirements",
        "dependencies and integrations",
        "error handling and fallback strategies",
        "testing strategy and qa",
        "rollout plan and deployment",
        "security and privacy",
        "ownership and team",
    ]

    count, found = _detect_core_sections(sections)

    assert count == 9
    assert len(found) == 9
    assert "goals_scope" in found
    assert "success_metrics" in found
    assert "nonfunctional_reqs" in found
    assert "dependencies" in found
    assert "error_handling" in found
    assert "testing" in found
    assert "rollout" in found
    assert "security" in found
    assert "ownership" in found


def test_maturity_score_calculation() -> None:
    """Test score calculation formula."""
    metrics = MaturityMetrics(
        char_count=3000,  # 20 points (2000-5000 range)
        section_count=7,  # 20 points (6-10 range)
        core_sections_present=5,  # ~28 points (5/9 * 50)
        core_sections_found=["goals_scope", "testing", "security", "dependencies", "rollout"],
    )

    score = _calculate_score(metrics)

    # Should be ~20 (length) + 20 (sections) + ~28 (5/9 * 50) = 68
    assert 65 <= score <= 70


def test_maturity_score_calculation_edge_cases() -> None:
    """Test score calculation edge cases."""
    # Empty document
    empty_metrics = MaturityMetrics(
        char_count=0, section_count=0, core_sections_present=0, core_sections_found=[]
    )
    assert _calculate_score(empty_metrics) == 0

    # Maximum score
    max_metrics = MaturityMetrics(
        char_count=10000,
        section_count=15,
        core_sections_present=9,
        core_sections_found=["all"] * 9,
    )
    score = _calculate_score(max_metrics)
    assert score == 100  # Capped at 100


def test_maturity_level_determination() -> None:
    """Test level mapping from scores."""
    assert _determine_level(0) == "notes"
    assert _determine_level(10) == "notes"
    assert _determine_level(24) == "notes"
    assert _determine_level(25) == "early_draft"
    assert _determine_level(35) == "early_draft"
    assert _determine_level(49) == "early_draft"
    assert _determine_level(50) == "design_spec"
    assert _determine_level(60) == "design_spec"
    assert _determine_level(74) == "design_spec"
    assert _determine_level(75) == "production_ready"
    assert _determine_level(90) == "production_ready"
    assert _determine_level(100) == "production_ready"


def test_maturity_confidence_calculation() -> None:
    """Test confidence levels based on thresholds."""
    # High confidence: clearly in one level
    assert _calculate_confidence(5) == "high"  # Clearly notes
    assert _calculate_confidence(10) == "high"
    assert _calculate_confidence(90) == "high"  # Clearly production-ready
    assert _calculate_confidence(95) == "high"

    # Low confidence: near threshold boundaries
    assert _calculate_confidence(20) == "low"  # Near 25 threshold
    assert _calculate_confidence(25) == "low"
    assert _calculate_confidence(30) == "low"
    assert _calculate_confidence(45) == "low"  # Near 50 threshold
    assert _calculate_confidence(50) == "low"
    assert _calculate_confidence(55) == "low"
    assert _calculate_confidence(70) == "low"  # Near 75 threshold
    assert _calculate_confidence(75) == "low"
    assert _calculate_confidence(80) == "low"

    # Medium confidence: mid-range
    assert _calculate_confidence(15) == "medium"
    assert _calculate_confidence(40) == "medium"
    assert _calculate_confidence(65) == "medium"
    assert _calculate_confidence(85) == "medium"


def test_maturity_signal_generation() -> None:
    """Test signal generation for various scenarios."""
    # Very short document with no core sections
    metrics1 = MaturityMetrics(
        char_count=100, section_count=1, core_sections_present=0, core_sections_found=[]
    )
    signals1 = _generate_signals(metrics1, [])
    assert "very_short_length" in signals1
    assert "missing_most_core_sections" in signals1
    assert "missing_goals" in signals1
    assert "missing_metrics" in signals1
    assert "missing_testing" in signals1

    # Comprehensive document
    metrics2 = MaturityMetrics(
        char_count=6000,
        section_count=12,
        core_sections_present=8,
        core_sections_found=[
            "goals_scope",
            "success_metrics",
            "testing",
            "security",
            "dependencies",
            "rollout",
            "nonfunctional_reqs",
            "error_handling",
        ],
    )
    signals2 = _generate_signals(
        metrics2,
        [
            "goals_scope",
            "success_metrics",
            "testing",
            "security",
            "dependencies",
            "rollout",
            "nonfunctional_reqs",
            "error_handling",
        ],
    )
    assert "comprehensive_length" in signals2
    assert "many_sections" in signals2
    assert "comprehensive_coverage" in signals2
    assert "missing_goals" not in signals2
    assert "missing_metrics" not in signals2
    assert "missing_testing" not in signals2


def test_maturity_interpretation_strings() -> None:
    """Test interpretation text for each level."""
    assert "early-stage notes" in _get_interpretation("notes")
    assert "Incomplete sections" in _get_interpretation("early_draft")
    assert "substantial" in _get_interpretation("design_spec")
    assert "Comprehensive document" in _get_interpretation("production_ready")
    assert "could not be determined" in _get_interpretation("invalid_level")


def test_maturity_empty_document() -> None:
    """Test edge case: empty document."""
    content = ""
    sections = []

    result = compute_maturity(content, sections)

    assert result.level == "notes"
    assert result.score == 0
    assert "very_short_length" in result.signals or "no_sections_detected" in result.signals
    assert result.confidence == "high"


def test_maturity_single_long_section() -> None:
    """Test edge case: single long section without structure."""
    content = "# Design\n" + ("A" * 10000)
    sections = ["design", "a" * 100]  # Long content but minimal structure

    result = compute_maturity(content, sections)

    # Should be early_draft due to high length but minimal sections/structure
    assert result.level in ("early_draft", "design_spec")
    assert result.metrics.char_count > 10000
    assert result.metrics.section_count <= 2


def test_maturity_many_sections_but_short() -> None:
    """Test edge case: many sections but very short content."""
    content = "# A\n# B\n# C\n# D\n# E\n# F\n# G\n# H\n# I\n# J"
    sections = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]

    result = compute_maturity(content, sections)

    # Should cap at early_draft due to very short length despite many sections
    assert result.level in ("notes", "early_draft")
    assert result.metrics.section_count >= 10
    assert result.metrics.char_count < 200


def test_maturity_all_core_sections_but_short() -> None:
    """Test edge case: has all core sections but minimal content."""
    content = """
# Goals
TBD
# Metrics
TBD
# Performance
TBD
# Dependencies
TBD
# Errors
TBD
# Testing
TBD
# Rollout
TBD
# Security
TBD
# Owner
TBD
"""
    sections = [
        "goals",
        "metrics",
        "performance",
        "dependencies",
        "errors",
        "testing",
        "rollout",
        "security",
        "owner",
    ]

    result = compute_maturity(content, sections)

    # Should be design_spec due to core section coverage
    # but limited by short length
    assert result.level in ("early_draft", "design_spec")
    assert result.metrics.core_sections_present == 9


def test_maturity_threshold_boundary() -> None:
    """Test scoring right at threshold boundaries."""
    # Score exactly at 25 (notes/early_draft boundary)
    metrics_25 = MaturityMetrics(
        char_count=500,  # 10 points
        section_count=3,  # 10 points
        core_sections_present=1,  # ~5 points
        core_sections_found=["goals_scope"],
    )
    score_25 = _calculate_score(metrics_25)
    level_25 = _determine_level(score_25)
    assert level_25 == "early_draft"

    # Score exactly at 50 (early_draft/design_spec boundary)
    metrics_50 = MaturityMetrics(
        char_count=2000,  # 20 points
        section_count=6,  # 20 points
        core_sections_present=2,  # ~11 points
        core_sections_found=["goals_scope", "testing"],
    )
    score_50 = _calculate_score(metrics_50)
    level_50 = _determine_level(score_50)
    assert level_50 == "design_spec"
