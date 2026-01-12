"""Document maturity assessment module."""

from dataclasses import dataclass


@dataclass
class MaturityMetrics:
    """Metrics used to compute document maturity."""

    char_count: int
    section_count: int
    core_sections_present: int
    core_sections_found: list[str]


@dataclass
class MaturityResult:
    """Result of document maturity assessment."""

    level: str  # "notes", "early_draft", "design_spec", "production_ready"
    score: int  # 0-100
    confidence: str  # "low", "medium", "high"
    interpretation: str
    signals: list[str]
    metrics: MaturityMetrics


# Core section patterns (9 total sections to detect)
CORE_SECTION_PATTERNS = {
    "goals_scope": ["goal", "objective", "scope", "purpose"],
    "success_metrics": ["success", "metric", "kpi", "measure"],
    "nonfunctional_reqs": ["performance", "scalability", "reliability", "sla"],
    "dependencies": ["dependency", "dependencies", "integration", "external"],
    "error_handling": ["error", "exception", "failure", "fallback"],
    "testing": ["test", "testing", "qa", "validation"],
    "rollout": ["rollout", "deployment", "migration", "rollback"],
    "security": ["security", "auth", "privacy", "data retention"],
    "ownership": ["owner", "team", "on-call", "support"],
}


def compute_maturity(content: str, sections: list[str]) -> MaturityResult:
    """
    Compute document maturity based on content and sections.

    Args:
        content: Full document content (already redacted)
        sections: Extracted section headers (lowercase)

    Returns:
        MaturityResult with level, score, confidence, signals
    """
    # Gather metrics
    char_count = len(content)
    section_count = len(sections)
    core_sections_present, core_sections_found = _detect_core_sections(sections)

    metrics = MaturityMetrics(
        char_count=char_count,
        section_count=section_count,
        core_sections_present=core_sections_present,
        core_sections_found=core_sections_found,
    )

    # Calculate score
    score = _calculate_score(metrics)

    # Determine level
    level = _determine_level(score)

    # Calculate confidence
    confidence = _calculate_confidence(score)

    # Generate signals
    signals = _generate_signals(metrics, core_sections_found)

    # Get interpretation
    interpretation = _get_interpretation(level)

    return MaturityResult(
        level=level,
        score=score,
        confidence=confidence,
        interpretation=interpretation,
        signals=signals,
        metrics=metrics,
    )


def _detect_core_sections(sections: list[str]) -> tuple[int, list[str]]:
    """
    Detect presence of 9 core sections.

    Args:
        sections: List of section headers (lowercase)

    Returns:
        Tuple of (count_present, list_of_found_section_names)
    """
    found = []

    for section_name, patterns in CORE_SECTION_PATTERNS.items():
        # Check if any pattern matches any section
        for section in sections:
            if any(pattern in section for pattern in patterns):
                found.append(section_name)
                break

    return len(found), found


def _calculate_score(metrics: MaturityMetrics) -> int:
    """
    Calculate 0-100 maturity score from metrics.

    Formula:
    - Document length: 0-25 points
    - Section count: 0-25 points
    - Core section coverage: 0-50 points

    Args:
        metrics: MaturityMetrics

    Returns:
        Score from 0-100
    """
    score = 0

    # 1. Document Length (0-25 points)
    if metrics.char_count >= 5000:
        score += 25
    elif metrics.char_count >= 2000:
        score += 20
    elif metrics.char_count >= 500:
        score += 10
    elif metrics.char_count >= 200:
        score += 5
    # else: 0 points

    # 2. Section Count (0-25 points)
    if metrics.section_count >= 10:
        score += 25
    elif metrics.section_count >= 6:
        score += 20
    elif metrics.section_count >= 3:
        score += 10
    elif metrics.section_count >= 1:
        score += 5
    # else: 0 points

    # 3. Core Section Coverage (0-50 points)
    # Each core section present = 50/9 ≈ 5.56 points
    score += int((metrics.core_sections_present / 9.0) * 50)

    # Cap at 100
    return min(100, score)


def _determine_level(score: int) -> str:
    """
    Map score to maturity level.

    Args:
        score: Maturity score (0-100)

    Returns:
        Level name: "notes", "early_draft", "design_spec", or "production_ready"
    """
    if score >= 75:
        return "production_ready"
    elif score >= 50:
        return "design_spec"
    elif score >= 25:
        return "early_draft"
    else:
        return "notes"


def _calculate_confidence(score: int) -> str:
    """
    Determine confidence based on proximity to thresholds.

    Confidence is "low" when score is near threshold boundaries,
    "high" when clearly in a level, "medium" otherwise.

    Args:
        score: Maturity score (0-100)

    Returns:
        Confidence level: "low", "medium", or "high"
    """
    # High confidence: clearly notes (<=10) or production-ready (>=90)
    if score <= 10 or score >= 90:
        return "high"

    # Low confidence: near threshold boundaries
    # Thresholds: 25 (notes/early_draft), 50 (early_draft/design_spec), 75 (design_spec/prod)
    if (20 <= score <= 30) or (45 <= score <= 55) or (70 <= score <= 80):
        return "low"

    # Medium confidence: mid-range within a level
    return "medium"


def _generate_signals(metrics: MaturityMetrics, core_sections_found: list[str]) -> list[str]:
    """
    Generate list of signals explaining the maturity assessment.

    Args:
        metrics: MaturityMetrics
        core_sections_found: List of found core section names

    Returns:
        List of signal strings
    """
    signals = []

    # Length signals
    if metrics.char_count < 200:
        signals.append("very_short_length")
    elif metrics.char_count < 500:
        signals.append("short_length")
    elif metrics.char_count > 5000:
        signals.append("comprehensive_length")

    # Section signals
    if metrics.section_count == 0:
        signals.append("no_sections_detected")
    elif metrics.section_count <= 2:
        signals.append("few_sections")
    elif metrics.section_count >= 10:
        signals.append("many_sections")

    # Core section signals
    missing_critical = 9 - metrics.core_sections_present
    if missing_critical >= 7:
        signals.append("missing_most_core_sections")
    elif missing_critical >= 4:
        signals.append("missing_many_core_sections")
    elif missing_critical <= 2:
        signals.append("comprehensive_coverage")

    # Specific missing sections
    if "goals_scope" not in core_sections_found:
        signals.append("missing_goals")
    if "success_metrics" not in core_sections_found:
        signals.append("missing_metrics")
    if "testing" not in core_sections_found:
        signals.append("missing_testing")

    return signals


def _get_interpretation(level: str) -> str:
    """
    Get user-facing interpretation text for each level.

    Args:
        level: Maturity level name

    Returns:
        Interpretation string for display
    """
    interpretations = {
        "notes": (
            "This appears to be early-stage notes or brainstorming. "
            "Comprehensive findings are expected and helpful for planning."
        ),
        "early_draft": (
            "Incomplete sections are expected at this stage. Focus on high-severity gaps."
        ),
        "design_spec": (
            "Document is substantial with good coverage of core areas. "
            "Findings indicate areas needing attention before implementation."
        ),
        "production_ready": (
            "Comprehensive document with thorough coverage. "
            "Findings are refinements rather than gaps."
        ),
    }

    return interpretations.get(level, "Document maturity could not be determined.")
