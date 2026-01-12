"""Baseline comparison logic."""

from dataclasses import dataclass

from tiresias.schemas.report import Finding, Severity


@dataclass(frozen=True)
class FindingKey:
    """Unique identifier for a finding."""

    rule_id: str
    category: str

    @classmethod
    def from_finding(cls, finding: Finding) -> "FindingKey":
        """Create FindingKey from a Finding."""
        return cls(rule_id=finding.id, category=finding.category.value)


def compare_findings(
    current_findings: list[Finding],
    baseline_findings: list[Finding],
) -> tuple[
    list[Finding],
    list[tuple[Finding, Severity]],
    list[Finding],
    list[tuple[Finding, Severity]],
]:
    """
    Compare current findings against baseline.

    Args:
        current_findings: Findings from current analysis
        baseline_findings: Findings from baseline analysis

    Returns:
        Tuple of (new, worsened, unchanged, improved)
        - new: Findings present in current but not baseline
        - worsened: Findings with increased severity (finding, baseline_severity)
        - unchanged: Findings with same severity
        - improved: Findings with decreased severity (finding, baseline_severity)
    """
    # Build lookup maps
    baseline_map = {FindingKey.from_finding(f): f for f in baseline_findings}
    current_map = {FindingKey.from_finding(f): f for f in current_findings}

    # Severity ordering
    severity_order = {Severity.LOW: 1, Severity.MEDIUM: 2, Severity.HIGH: 3}

    new: list[Finding] = []
    worsened: list[tuple[Finding, Severity]] = []
    unchanged: list[Finding] = []
    improved: list[tuple[Finding, Severity]] = []

    # Check current findings
    for key, current_f in current_map.items():
        if key not in baseline_map:
            # New finding
            new.append(current_f)
        else:
            # Compare severity
            baseline_f = baseline_map[key]
            curr_sev = severity_order[current_f.severity]
            base_sev = severity_order[baseline_f.severity]

            if curr_sev > base_sev:
                worsened.append((current_f, baseline_f.severity))
            elif curr_sev < base_sev:
                improved.append((current_f, baseline_f.severity))
            else:
                unchanged.append(current_f)

    return new, worsened, unchanged, improved


def check_maturity_regression(current_score: int, baseline_score: int) -> bool:
    """
    Check if document maturity has regressed.

    Args:
        current_score: Current maturity score (0-100)
        baseline_score: Baseline maturity score (0-100)

    Returns:
        True if maturity decreased
    """
    return current_score < baseline_score
