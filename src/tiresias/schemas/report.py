"""Report schema for Tiresias analysis output."""

from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Finding severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Category(str, Enum):
    """Finding categories."""

    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    OPERATIONS = "operations"
    SECURITY = "security"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    DOCUMENTATION = "documentation"


class Finding(BaseModel):
    """A single analysis finding."""

    id: str = Field(..., description="Unique finding ID (e.g., REQ-001)")
    title: str = Field(..., description="Short summary of the finding")
    severity: Severity = Field(..., description="Severity level")
    category: Category = Field(..., description="Category of the finding")
    evidence: str = Field(..., description="Where/why this was flagged")
    impact: str = Field(..., description="What could go wrong")
    recommendation: str = Field(..., description="How to address it")


class Metadata(BaseModel):
    """Report metadata."""

    tool_version: str = Field(..., description="Tiresias version")
    timestamp: str = Field(..., description="ISO8601 timestamp")
    input_files: list[str] = Field(..., description="List of analyzed files")
    profile: str = Field(..., description="Analysis profile used")
    model_provider: str = Field(
        default="heuristic",
        description="Analysis provider (heuristic or future LLM)",
    )
    elapsed_ms: int = Field(..., description="Analysis duration in milliseconds")


class MaturityMetrics(BaseModel):
    """Metrics used to compute document maturity."""

    char_count: int = Field(..., description="Total character count")
    section_count: int = Field(..., description="Number of sections detected")
    core_sections_present: int = Field(..., description="Count of core sections found")
    core_sections_found: list[str] = Field(..., description="Names of found core sections")


class Maturity(BaseModel):
    """Document maturity assessment."""

    level: str = Field(
        ..., description="Maturity level (notes, early_draft, design_spec, production_ready)"
    )
    score: int = Field(..., ge=0, le=100, description="Maturity score 0-100")
    confidence: str = Field(..., description="Confidence level (low, medium, high)")
    interpretation: str = Field(..., description="User-facing interpretation of maturity level")
    signals: list[str] = Field(..., description="List of signals that informed the assessment")
    metrics: MaturityMetrics = Field(..., description="Detailed metrics")


class FindingChange(str, Enum):
    """Type of change relative to baseline."""

    NEW = "new"
    WORSENED = "worsened"
    UNCHANGED = "unchanged"
    IMPROVED = "improved"


class FindingComparison(BaseModel):
    """Comparison of a finding against baseline."""

    finding: Finding = Field(..., description="The finding")
    change: FindingChange = Field(..., description="Type of change")
    baseline_severity: Severity | None = Field(
        None,
        description="Severity in baseline (None if new)",
    )


class BaselineSummary(BaseModel):
    """Summary of baseline analysis."""

    git_ref: str = Field(..., description="Git reference analyzed")
    commit_sha: str = Field(..., description="Resolved commit SHA")
    findings_count: int = Field(..., description="Total findings in baseline")
    risk_score: int = Field(..., description="Risk score of baseline")
    maturity_score: int = Field(..., description="Maturity score of baseline")


class ComparisonResult(BaseModel):
    """Result of baseline comparison."""

    baseline_summary: BaselineSummary = Field(..., description="Summary of baseline")
    new_findings: list[Finding] = Field(..., description="Findings not in baseline")
    worsened_findings: list[FindingComparison] = Field(
        ...,
        description="Findings with increased severity",
    )
    unchanged_findings: list[Finding] = Field(
        ...,
        description="Findings with same severity",
    )
    improved_findings: list[FindingComparison] = Field(
        ...,
        description="Findings with decreased severity or resolved",
    )
    maturity_regressed: bool = Field(
        ...,
        description="True if maturity score decreased",
    )


class ReviewReport(BaseModel):
    """Complete analysis report."""

    metadata: Metadata = Field(..., description="Report metadata")
    maturity: Maturity = Field(..., description="Document maturity assessment")
    findings: list[Finding] = Field(..., description="List of findings")
    assumptions: list[str] = Field(..., description="Identified assumptions")
    open_questions: list[str] = Field(..., description="Open questions found")
    quick_summary: list[str] = Field(..., description="3-5 bullet summary")
    risk_score: int = Field(..., ge=0, le=100, description="Overall risk score 0-100")
    risk_score_explanation: str = Field(..., description="Explanation of risk score calculation")
    baseline_ref: str | None = Field(
        None,
        description="Git ref used for baseline comparison",
    )
    comparison: ComparisonResult | None = Field(
        None,
        description="Baseline comparison results (only if baseline provided)",
    )

    model_config = {"json_schema_extra": {"title": "TiresiasReviewReport"}}
