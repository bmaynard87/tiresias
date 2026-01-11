"""Risk scoring calculation."""

from collections import Counter

from tiresias.schemas.report import Finding, Severity


def calculate_risk_score(
    findings: list[Finding],
    category_weights: dict[str, float],
) -> tuple[int, str]:
    """
    Calculate overall risk score from findings.

    Args:
        findings: List of findings
        category_weights: Weight multipliers per category

    Returns:
        Tuple of (risk_score, explanation)
    """
    # Severity point values
    severity_points = {
        Severity.HIGH: 15,
        Severity.MEDIUM: 8,
        Severity.LOW: 3,
    }

    # Calculate weighted score
    total_score = 0.0
    severity_counts = Counter()

    for finding in findings:
        base_points = severity_points[finding.severity]
        weight = category_weights.get(finding.category.value, 1.0)
        total_score += base_points * weight
        severity_counts[finding.severity] += 1

    # Cap at 100
    risk_score = min(100, int(total_score))

    # Generate explanation
    explanation = _generate_explanation(risk_score, severity_counts, findings)

    return risk_score, explanation


def _generate_explanation(
    score: int,
    severity_counts: Counter,
    findings: list[Finding],
) -> str:
    """Generate human-readable explanation of risk score."""
    # Determine risk band
    if score <= 20:
        band = "Low"
    elif score <= 50:
        band = "Medium"
    elif score <= 80:
        band = "High"
    else:
        band = "Critical"

    lines = [f"Risk score: {score}/100 ({band})"]

    # Severity breakdown
    high_count = severity_counts[Severity.HIGH]
    med_count = severity_counts[Severity.MEDIUM]
    low_count = severity_counts[Severity.LOW]

    severity_parts = []
    if high_count:
        severity_parts.append(f"{high_count} high-severity")
    if med_count:
        severity_parts.append(f"{med_count} medium")
    if low_count:
        severity_parts.append(f"{low_count} low")

    if severity_parts:
        lines.append(f"Based on {', '.join(severity_parts)} finding(s).")

    # Highlight top issues
    high_findings = [f for f in findings if f.severity == Severity.HIGH]
    if high_findings:
        top_issues = [f.title for f in high_findings[:3]]
        lines.append(f"Primary risks: {', '.join(top_issues)}.")

    return " ".join(lines)
