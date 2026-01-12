"""Suppression engine for filtering findings based on .tiresias.yml config."""

from datetime import UTC, date, datetime
from fnmatch import fnmatch

from tiresias.schemas.config import SuppressionEntry, TiresiasConfig
from tiresias.schemas.report import (
    ExpiredSuppression,
    Finding,
    Severity,
    SuppressedSummary,
    SuppressionInfo,
)


class SuppressionResult:
    """Result of applying suppressions to findings."""

    def __init__(
        self,
        visible_findings: list[Finding],
        suppressed_findings: list[Finding],
        expired_suppressions: list[ExpiredSuppression],
        warnings: list[str],
    ):
        self.visible_findings = visible_findings
        self.suppressed_findings = suppressed_findings
        self.expired_suppressions = expired_suppressions
        self.warnings = warnings

    def get_suppressed_summary(self) -> SuppressedSummary | None:
        """Generate suppressed findings summary."""
        if not self.suppressed_findings:
            return None

        by_severity = {
            "high": sum(1 for f in self.suppressed_findings if f.severity == Severity.HIGH),
            "medium": sum(1 for f in self.suppressed_findings if f.severity == Severity.MEDIUM),
            "low": sum(1 for f in self.suppressed_findings if f.severity == Severity.LOW),
        }

        return SuppressedSummary(
            total=len(self.suppressed_findings),
            by_severity=by_severity,
        )


def apply_suppressions(
    findings: list[Finding],
    config: TiresiasConfig,
    profile: str,
    input_files: list[str],
) -> SuppressionResult:
    """
    Apply suppressions from config to findings.

    Args:
        findings: All findings from analysis
        config: Loaded configuration with suppressions
        profile: Current analysis profile
        input_files: List of file paths being analyzed

    Returns:
        SuppressionResult with visible/suppressed findings and metadata
    """
    if not config.suppressions:
        return SuppressionResult(
            visible_findings=findings,
            suppressed_findings=[],
            expired_suppressions=[],
            warnings=[],
        )

    today = datetime.now(UTC).date()

    # Validate suppressions and collect expired ones
    active_suppressions: list[SuppressionEntry] = []
    expired_suppressions: list[ExpiredSuppression] = []
    warnings: list[str] = []

    for suppression in config.suppressions:
        # Check if expired
        if suppression.expires:
            expiry_date = date.fromisoformat(suppression.expires)
            if expiry_date < today:
                expired_suppressions.append(
                    ExpiredSuppression(
                        id=suppression.id,
                        expires=suppression.expires,
                        reason=suppression.reason,
                    )
                )
                continue

        active_suppressions.append(suppression)

    # Apply active suppressions
    visible_findings: list[Finding] = []
    suppressed_findings: list[Finding] = []

    for finding in findings:
        suppression_match = _find_matching_suppression(
            finding,
            active_suppressions,
            profile,
            input_files,
        )

        if suppression_match:
            # Mark as suppressed
            finding.suppressed = True
            finding.suppression = SuppressionInfo(
                reason=suppression_match.reason,
                expires=suppression_match.expires,
                scope=suppression_match.scope,
                profiles=suppression_match.profiles,
                severities=suppression_match.severities,
            )
            suppressed_findings.append(finding)
        else:
            visible_findings.append(finding)

    return SuppressionResult(
        visible_findings=visible_findings,
        suppressed_findings=suppressed_findings,
        expired_suppressions=expired_suppressions,
        warnings=warnings,
    )


def _find_matching_suppression(
    finding: Finding,
    suppressions: list[SuppressionEntry],
    profile: str,
    input_files: list[str],
) -> SuppressionEntry | None:
    """Find first suppression that matches this finding."""
    for suppression in suppressions:
        if _suppression_matches_finding(finding, suppression, profile, input_files):
            return suppression
    return None


def _suppression_matches_finding(
    finding: Finding,
    suppression: SuppressionEntry,
    profile: str,
    input_files: list[str],
) -> bool:
    """Check if suppression applies to this finding."""
    # Rule ID must match
    if finding.id != suppression.id:
        return False

    # Profile filter (if specified)
    if suppression.profiles:
        if profile not in suppression.profiles:
            return False

    # Severity filter (if specified)
    if suppression.severities:
        if finding.severity.value not in suppression.severities:
            return False

    # Scope filter (if specified)
    if suppression.scope:
        # At least one input file must match a scope glob
        if not _any_file_matches_scope(input_files, suppression.scope):
            return False

    return True


def _any_file_matches_scope(
    input_files: list[str],
    scope_globs: list[str],
) -> bool:
    """Check if any input file matches at least one scope glob."""
    for file_path in input_files:
        for glob_pattern in scope_globs:
            if fnmatch(file_path, glob_pattern):
                return True
    return False
