"""Heuristic analysis engine."""

import re
from collections.abc import Callable
from dataclasses import dataclass

from tiresias.schemas.report import Category, Finding, Severity


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


@dataclass
class AnalysisRule:
    """Definition of a single analysis rule."""

    id: str
    title: str
    severity: Severity
    category: Category
    evidence_template: str
    impact: str
    recommendation: str
    detect_fn: Callable[[str, list[str]], bool]


class HeuristicAnalyzer:
    """Heuristic-based document analyzer."""

    def __init__(self) -> None:
        """Initialize analyzer with rule set."""
        self.rules = self._build_rules()

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

    def _build_rules(self) -> list[AnalysisRule]:
        """Build the complete rule set."""
        return [
            # REQ-001: Missing success metrics
            AnalysisRule(
                id="REQ-001",
                title="Missing success metrics",
                severity=Severity.HIGH,
                category=Category.REQUIREMENTS,
                evidence_template="No section found discussing success criteria, metrics, or KPIs",
                impact=(
                    "Without measurable success criteria, it will be difficult to determine "
                    "if the implementation achieves its goals or to make data-driven decisions"
                ),
                recommendation=(
                    "Add a section defining concrete success metrics "
                    "(e.g., adoption rate, performance targets, user satisfaction scores)"
                ),
                detect_fn=lambda c, s: any(
                    re.search(
                        r"success\s+(?:criteria|metrics)|kpi|key\s+performance|measure\s+success",
                        section,
                    )
                    for section in s
                ),
            ),
            # REQ-002: Unclear scope/goals
            AnalysisRule(
                id="REQ-002",
                title="Unclear scope or goals",
                severity=Severity.MEDIUM,
                category=Category.REQUIREMENTS,
                evidence_template="No clear section defining goals, objectives, or scope",
                impact=(
                    "Ambiguous scope increases risk of scope creep, misaligned expectations, "
                    "and wasted effort on out-of-scope work"
                ),
                recommendation=(
                    "Add a dedicated section outlining specific goals, objectives, "
                    "and explicit scope boundaries (in-scope and out-of-scope)"
                ),
                detect_fn=lambda c, s: any(
                    re.search(r"(?:goal|objective|scope|purpose)", section) for section in s
                ),
            ),
            # REQ-003: Missing non-functional requirements
            AnalysisRule(
                id="REQ-003",
                title="Missing non-functional requirements",
                severity=Severity.MEDIUM,
                category=Category.REQUIREMENTS,
                evidence_template=(
                    "No discussion of performance, scalability, reliability, or SLA requirements"
                ),
                impact=(
                    "Lack of non-functional requirements may lead to systems that are "
                    "functionally correct but fail under load or don't meet user expectations"
                ),
                recommendation=(
                    "Document expected performance targets, scalability needs, "
                    "reliability requirements, and any SLAs"
                ),
                detect_fn=lambda c, s: any(
                    re.search(
                        r"performance|scalability|reliability|availability|sla|latency|throughput",
                        section,
                    )
                    for section in s
                ),
            ),
            # ARCH-001: Missing error handling strategy
            AnalysisRule(
                id="ARCH-001",
                title="Missing error handling strategy",
                severity=Severity.HIGH,
                category=Category.ARCHITECTURE,
                evidence_template=(
                    "No discussion of error handling, exceptions, failures, or fallback strategies"
                ),
                impact=(
                    "Without a defined error handling strategy, the system may fail ungracefully, "
                    "provide poor user experience, or lose data"
                ),
                recommendation=(
                    "Document error scenarios, handling strategies, retry logic, "
                    "fallback mechanisms, and user-facing error messaging"
                ),
                detect_fn=lambda c, s: any(
                    re.search(r"error|exception|failure|fallback|retry|graceful", section)
                    for section in s
                ),
            ),
            # ARCH-002: Unclear dependencies
            AnalysisRule(
                id="ARCH-002",
                title="Unclear dependencies",
                severity=Severity.MEDIUM,
                category=Category.ARCHITECTURE,
                evidence_template=(
                    "No clear discussion of dependencies, integrations, or external systems"
                ),
                impact=(
                    "Unclear dependencies can lead to integration surprises, "
                    "blocked work, or architectural mismatches"
                ),
                recommendation=(
                    "List all external dependencies (services, APIs, libraries), "
                    "integration points, and any assumptions about their behavior"
                ),
                detect_fn=lambda c, s: any(
                    re.search(
                        r"dependenc|integration|external\s+system|third[- ]party|api",
                        section,
                    )
                    for section in s
                ),
            ),
            # ARCH-003: Missing data retention/privacy plan
            AnalysisRule(
                id="ARCH-003",
                title="Missing data retention/privacy plan",
                severity=Severity.HIGH,
                category=Category.ARCHITECTURE,
                evidence_template=(
                    "Document mentions data/user information but lacks retention "
                    "or privacy discussion"
                ),
                impact=(
                    "Missing data governance can lead to compliance violations (GDPR, CCPA), "
                    "security risks, and legal liability"
                ),
                recommendation=(
                    "Document data retention policies, privacy considerations, "
                    "PII handling, and compliance requirements"
                ),
                detect_fn=lambda c, s: (
                    # Return True (satisfied) if privacy IS discussed OR no data keywords
                    any(
                        re.search(
                            r"retention|gdpr|privacy|pii|personal\s+(?:data|information)|data\s+protection",
                            section,
                        )
                        for section in s
                    )
                    or not bool(
                        re.search(
                            r"(?:user|customer)\s+(?:data|information)|database|store|persist",
                            c.lower(),
                        )
                    )
                ),
            ),
            # TEST-001: Missing test strategy
            AnalysisRule(
                id="TEST-001",
                title="Missing test strategy",
                severity=Severity.MEDIUM,
                category=Category.TESTING,
                evidence_template="No discussion of testing approach, QA, or validation strategy",
                impact=(
                    "Without a test strategy, quality may suffer, regressions may go undetected, "
                    "and confidence in releases will be low"
                ),
                recommendation=(
                    "Define testing approach (unit, integration, e2e), "
                    "coverage targets, and validation criteria"
                ),
                detect_fn=lambda c, s: any(
                    re.search(r"test|qa|quality|validation|verification", section) for section in s
                ),
            ),
            # OPS-001: Missing rollout plan
            AnalysisRule(
                id="OPS-001",
                title="Missing rollout/deployment plan",
                severity=Severity.HIGH,
                category=Category.OPERATIONS,
                evidence_template=(
                    "No discussion of rollout, deployment, migration, or rollback strategy"
                ),
                impact=(
                    "Without a deployment plan, rollouts may be risky, uncoordinated, "
                    "or lack rollback capability, leading to incidents"
                ),
                recommendation=(
                    "Document rollout strategy (phased, feature flags, canary), "
                    "deployment steps, monitoring, and rollback procedures"
                ),
                detect_fn=lambda c, s: any(
                    re.search(
                        r"rollout|deploy|migration|rollback|release\s+plan|launch\s+plan",
                        section,
                    )
                    for section in s
                ),
            ),
            # OPS-002: Unclear ownership
            AnalysisRule(
                id="OPS-002",
                title="Unclear ownership",
                severity=Severity.MEDIUM,
                category=Category.OPERATIONS,
                evidence_template="No clear owner, team, or on-call responsibility defined",
                impact=(
                    "Unclear ownership leads to confusion about who is responsible "
                    "for maintenance, incidents, and improvements"
                ),
                recommendation=(
                    "Identify the owning team, primary contacts, "
                    "and on-call/support responsibilities"
                ),
                detect_fn=lambda c, s: any(
                    re.search(
                        r"owner|team|responsible|maintainer|on[- ]call|support",
                        section,
                    )
                    for section in s
                ),
            ),
            # SEC-001: Missing security considerations
            AnalysisRule(
                id="SEC-001",
                title="Missing security considerations",
                severity=Severity.HIGH,
                category=Category.SECURITY,
                evidence_template=(
                    "Document appears to involve sensitive operations but lacks security discussion"
                ),
                impact=(
                    "Ignoring security considerations can lead to vulnerabilities, "
                    "data breaches, and compliance violations"
                ),
                recommendation=(
                    "Document authentication, authorization, encryption, "
                    "input validation, and security review requirements"
                ),
                detect_fn=lambda c, s: (
                    # Return True (satisfied) if security IS discussed OR no sensitive keywords
                    any(
                        re.search(
                            r"security|authentication|authorization|encryption|auth\b|access\s+control",
                            section,
                        )
                        for section in s
                    )
                    or not bool(
                        re.search(
                            r"user|account|credential|token|password|api|endpoint|request",
                            c.lower(),
                        )
                    )
                ),
            ),
            # PERF-001: Missing performance targets
            AnalysisRule(
                id="PERF-001",
                title="Missing performance targets",
                severity=Severity.LOW,
                category=Category.PERFORMANCE,
                evidence_template="No specific performance targets or latency requirements defined",
                impact=(
                    "Without performance targets, it's difficult to validate "
                    "if the implementation meets user expectations or to detect regressions"
                ),
                recommendation=(
                    "Define concrete performance targets "
                    "(e.g., p95 latency < 200ms, throughput > 1000 rps)"
                ),
                detect_fn=lambda c, s: any(
                    re.search(
                        r"latency|throughput|performance\s+target|response\s+time|p\d{2}",
                        section,
                    )
                    for section in s
                ),
            ),
            # DOC-001: Missing decision rationale
            AnalysisRule(
                id="DOC-001",
                title="Missing decision rationale",
                severity=Severity.LOW,
                category=Category.DOCUMENTATION,
                evidence_template="Design document lacks discussion of alternatives or trade-offs",
                impact=(
                    "Without documented alternatives and trade-offs, future maintainers won't "
                    "understand why decisions were made, leading to repeated debates"
                ),
                recommendation=(
                    "Document considered alternatives, trade-offs, "
                    "and the reasoning behind key decisions"
                ),
                detect_fn=lambda c, s: any(
                    re.search(
                        r"alternative|trade[- ]off|why\s+(?:not|we)|decision|rationale|considered",
                        section,
                    )
                    for section in s
                ),
            ),
        ]
