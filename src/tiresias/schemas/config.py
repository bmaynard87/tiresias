"""Configuration schema for .tiresias.yml."""

from datetime import date

from pydantic import BaseModel, Field, field_validator


class SuppressionEntry(BaseModel):
    """A single suppression rule."""

    id: str = Field(..., description="Rule ID to suppress (e.g., ARCH-001)")
    reason: str = Field(..., description="Human justification for suppression")
    expires: str | None = Field(None, description="Expiry date YYYY-MM-DD (optional)")
    scope: list[str] | None = Field(None, description="Glob patterns for file paths (optional)")
    profiles: list[str] | None = Field(
        None, description="Profiles where suppression applies (optional)"
    )
    severities: list[str] | None = Field(
        None, description="Severities where suppression applies (optional)"
    )

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Suppression reason cannot be empty")
        return v.strip()

    @field_validator("expires")
    @classmethod
    def expires_must_be_valid_date(cls, v: str | None) -> str | None:
        if v is None:
            return None
        try:
            date.fromisoformat(v)  # Validates YYYY-MM-DD format
            return v
        except ValueError as e:
            raise ValueError(f"expires must be in YYYY-MM-DD format, got: {v}") from e


class TiresiasConfig(BaseModel):
    """Schema for .tiresias.yml configuration file."""

    ignore_paths: list[str] = Field(
        default_factory=list,
        description="Glob patterns for files/directories to ignore",
    )
    default_profile: str = Field(
        default="general",
        description="Default analysis profile to use",
    )
    redact_patterns: list[str] = Field(
        default_factory=list,
        description="Additional regex patterns to redact from content",
    )
    category_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "requirements": 1.0,
            "architecture": 1.0,
            "testing": 1.0,
            "operations": 1.0,
            "security": 1.5,
            "performance": 0.8,
            "reliability": 1.2,
            "documentation": 0.5,
        },
        description="Weights for risk scoring by category",
    )
    suppressions: list[SuppressionEntry] = Field(
        default_factory=list,
        description="Finding suppressions with justification",
    )

    model_config = {"extra": "ignore"}
