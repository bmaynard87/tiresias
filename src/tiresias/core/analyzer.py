"""Heuristic analysis engine."""

import re

from tiresias.core.rules import AnalysisRule, get_all_rules
from tiresias.schemas.report import Finding, Severity


def extract_sections(content: str) -> list[str]:
    """
    Extract markdown section headers and their context.

    Args:
        content: Document text

    Returns:
        List of section titles (normalized to lowercase)
    """
    sections: list[str] = []
    lines = content.split("\n")

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Markdown headers
        if stripped.startswith("#"):
            header = re.sub(r"^#+\s*", "", stripped).strip().lower()
            sections.append(header)

            # Include first paragraph of section as context
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip().lower()
                if next_line:
                    sections.append(next_line)

    return sections


class HeuristicAnalyzer:
    """Heuristic-based document analyzer."""

    def __init__(self) -> None:
        """Initialize analyzer with rule set."""
        self.rules = get_all_rules()

    def analyze(
        self, content: str, profile: str = "general", sections: list[str] | None = None
    ) -> list[Finding]:
        """
        Analyze document content for design issues.

        Args:
            content: Document text content
            profile: Analysis profile (general, security, performance, reliability)
            sections: Pre-extracted sections (if None, will extract from content)

        Returns:
            List of findings
        """
        if sections is None:
            sections = extract_sections(content)
        active_rules = self._filter_rules_by_profile(profile)

        findings: list[Finding] = []
        for rule in active_rules:
            if not rule.detect_fn(content, sections):
                evidence = rule.evidence_template
                finding = Finding(
                    id=rule.id,
                    title=rule.title,
                    severity=rule.severity,
                    category=rule.category,
                    evidence=evidence,
                    impact=rule.impact,
                    recommendation=rule.recommendation,
                )
                findings.append(finding)

        # Sort for determinism: severity DESC, category ASC, title ASC
        severity_order = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2}
        findings.sort(
            key=lambda f: (
                severity_order[f.severity],
                f.category.value,
                f.title,
            )
        )

        return findings

    def extract_assumptions(self, content: str) -> list[str]:
        """
        Extract stated assumptions from content.

        Args:
            content: Document text

        Returns:
            List of assumption strings
        """
        assumptions: list[str] = []
        lines = content.split("\n")

        # Patterns indicating assumptions
        patterns = [
            r"(?:we\s+)?assum(?:e|ing)\s+(?:that\s+)?(.+)",
            r"given\s+that\s+(.+)",
            r"presuming\s+(.+)",
        ]

        for line in lines:
            line = line.strip()
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    assumption = match.group(1).strip()
                    if assumption and len(assumption) < 200:
                        assumptions.append(assumption)
                    break

        return assumptions[:10]  # Limit to top 10

    def extract_questions(self, content: str) -> list[str]:
        """
        Extract open questions from content.

        Args:
            content: Document text

        Returns:
            List of question strings
        """
        questions: list[str] = []
        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            # Look for question marks, TBD, TODO markers
            if "?" in line and len(line) < 200:
                questions.append(line)
            elif re.search(r"\b(TBD|TODO|FIXME)\b", line, re.IGNORECASE):
                if len(line) < 200:
                    questions.append(line)

        return questions[:15]  # Limit to top 15

    def _filter_rules_by_profile(self, profile: str) -> list[AnalysisRule]:
        """Filter rules based on analysis profile."""
        profile = profile.lower()

        if profile == "security":
            # Security-focused: requirements, specific arch, security, ops ownership
            included_prefixes: tuple[str, ...] = ("REQ-", "ARCH-003", "SEC-", "OPS-002")
            return [r for r in self.rules if r.id.startswith(included_prefixes)]

        elif profile == "performance":
            # Performance: architecture, performance, testing
            included_prefixes_perf: tuple[str, ...] = ("ARCH-", "PERF-", "TEST-")
            return [r for r in self.rules if r.id.startswith(included_prefixes_perf)]

        elif profile == "reliability":
            # Reliability: error handling, testing, operations, performance
            included_ids = {
                "ARCH-001",
                "TEST-001",
                "OPS-001",
                "OPS-002",
                "PERF-001",
            }
            return [r for r in self.rules if r.id in included_ids]

        else:  # general
            return self.rules
