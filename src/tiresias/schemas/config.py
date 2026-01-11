"""Configuration schema for .tiresias.yml."""

from pydantic import BaseModel, Field


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

    model_config = {"extra": "ignore"}
