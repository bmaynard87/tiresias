"""End-to-end integration tests."""

import json
from pathlib import Path

from typer.testing import CliRunner

from tiresias.cli.app import app


def test_e2e_basic_review(tmp_path: Path) -> None:
    """Test end-to-end review workflow."""
    # Create a sample design doc
    doc = tmp_path / "design.md"
    doc.write_text(
        """
# Payment Service Design

## Goals
Build a new payment processing service to handle transactions.

## Scope
In scope: credit card processing, refunds
Out of scope: cryptocurrency, international payments

## Architecture
We will use a REST API with PostgreSQL database.
The service will integrate with Stripe API.

## Success Metrics
- Process 1000 transactions per day
- 99.9% uptime
- Average response time < 500ms
"""
    )

    runner = CliRunner()
    result = runner.invoke(app, ["review", str(doc), "--format", "json"])

    assert result.exit_code == 0

    # Parse JSON output
    report = json.loads(result.stdout)

    # Basic structure checks
    assert "metadata" in report
    assert "findings" in report
    assert "risk_score" in report
    assert report["metadata"]["profile"] == "general"
    assert len(report["metadata"]["input_files"]) == 1

    # Should have some findings (missing error handling, etc.)
    assert len(report["findings"]) > 0

    # Risk score should be calculated
    assert 0 <= report["risk_score"] <= 100


def test_e2e_security_profile(tmp_path: Path) -> None:
    """Test security profile filtering."""
    doc = tmp_path / "api-design.md"
    doc.write_text(
        """
# API Design

## Overview
New REST API for user management.

## Endpoints
- POST /users - Create user
- GET /users/:id - Get user
"""
    )

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["review", str(doc), "--format", "json", "--profile", "security"],
    )

    assert result.exit_code == 0
    report = json.loads(result.stdout)

    # Security profile should flag missing security considerations
    assert any(
        "security" in f["id"].lower() or f["category"] == "security" for f in report["findings"]
    )


def test_e2e_severity_threshold(tmp_path: Path) -> None:
    """Test severity threshold filtering."""
    doc = tmp_path / "design.md"
    doc.write_text("# Minimal Design Doc\nSome content")

    runner = CliRunner()

    # Run with high threshold
    result = runner.invoke(
        app,
        ["review", str(doc), "--format", "json", "--severity-threshold", "high"],
    )

    assert result.exit_code == 0
    report = json.loads(result.stdout)

    # Should only show high severity findings
    if report["findings"]:
        assert all(f["severity"] == "high" for f in report["findings"])


def test_e2e_output_to_file(tmp_path: Path) -> None:
    """Test writing output to file."""
    doc = tmp_path / "design.md"
    doc.write_text("# Design\nContent")

    output_file = tmp_path / "report.json"

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "review",
            str(doc),
            "--format",
            "json",
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert output_file.exists()

    # Verify output file content
    report = json.loads(output_file.read_text())
    assert "metadata" in report
    assert "findings" in report


def test_e2e_text_output(tmp_path: Path) -> None:
    """Test text output format."""
    doc = tmp_path / "design.md"
    doc.write_text("# Design Document\nMinimal content")

    runner = CliRunner()
    result = runner.invoke(app, ["review", str(doc), "--format", "text"])

    assert result.exit_code == 0
    # Should contain expected sections
    assert "Tiresias" in result.stdout
    assert "Risk Score" in result.stdout


def test_e2e_maturity_notes_document(tmp_path: Path) -> None:
    """Test full pipeline with notes-level document."""
    doc = tmp_path / "notes.md"
    doc.write_text("# Idea\nQuick thought about feature X.")

    runner = CliRunner()
    result = runner.invoke(app, ["review", str(doc), "--format", "json"])

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["maturity"]["level"] == "notes"
    assert report["maturity"]["score"] < 25
    assert "very_short_length" in report["maturity"]["signals"]


def test_e2e_maturity_comprehensive_document(tmp_path: Path) -> None:
    """Test full pipeline with production-ready document."""
    doc = tmp_path / "comprehensive.md"
    doc.write_text(
        """
# Feature: Advanced Analytics Dashboard

## Goals and Objectives
Build an analytics dashboard with real-time data visualization,
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
    )

    runner = CliRunner()
    result = runner.invoke(app, ["review", str(doc), "--format", "json"])

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["maturity"]["level"] in ["design_spec", "production_ready"]
    assert report["maturity"]["score"] >= 50
    assert report["maturity"]["metrics"]["core_sections_present"] >= 7
