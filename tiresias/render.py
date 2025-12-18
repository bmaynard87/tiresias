from __future__ import annotations

from typing import Any, Mapping


def render_review_md(review: Mapping[str, Any]) -> str:
    findings = list(review.get("findings", []))

    lines: list[str] = []
    lines.append("# Tiresias Review")
    lines.append("")
    lines.append(f"## Overall Risk: {review.get('overall_risk', '')}")
    lines.append("")
    lines.append("## Summary")
    lines.append(str(review.get("summary", "")).strip())
    lines.append("")
    lines.append("## Findings")

    for idx, finding in enumerate(findings, start=1):
        title = str(finding.get("title", "")).strip()
        severity = str(finding.get("severity", "")).strip()
        description = str(finding.get("description", "")).strip()
        recommendation = str(finding.get("recommendation", "")).strip()

        lines.append(f"### {idx}. {title}")
        lines.append(f"- Severity: {severity}")
        lines.append(f"- Description: {description}")
        lines.append(f"- Recommendation: {recommendation}")
        lines.append("")

    return "\n".join(lines).rstrip()
