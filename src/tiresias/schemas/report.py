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


class ReviewReport(BaseModel):
    """Complete analysis report."""

    metadata: Metadata = Field(..., description="Report metadata")
    findings: list[Finding] = Field(..., description="List of findings")
    assumptions: list[str] = Field(..., description="Identified assumptions")
    open_questions: list[str] = Field(..., description="Open questions found")
    quick_summary: list[str] = Field(..., description="3-5 bullet summary")
    risk_score: int = Field(..., ge=0, le=100, description="Overall risk score 0-100")
    risk_score_explanation: str = Field(..., description="Explanation of risk score calculation")

    model_config = {"json_schema_extra": {"title": "TiresiasReviewReport"}}
