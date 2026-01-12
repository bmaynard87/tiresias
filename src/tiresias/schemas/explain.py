"""Schemas for explain command output."""

from pydantic import BaseModel, Field


class RuleExplanation(BaseModel):
    """Explanation of a single rule."""

    id: str = Field(..., description="Rule ID (e.g., REQ-001)")
    title: str = Field(..., description="Rule title")
    severity: str = Field(..., description="Severity level (low/medium/high)")
    category: str = Field(..., description="Category name")
    checks: str = Field(..., description="What the rule checks for")
    why: str = Field(..., description="Why this matters (impact)")
    how_to_fix: str = Field(..., description="How to address findings")
    pitfalls: str = Field(default="", description="Common pitfalls (may be empty)")


class RuleList(BaseModel):
    """List of all available rules."""

    rules: list[dict[str, str]] = Field(
        ...,
        description="List of rules with id and title",
    )
