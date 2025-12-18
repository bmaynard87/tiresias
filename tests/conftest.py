from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import pytest


@dataclass(frozen=True)
class FakeProvider:
    overall_risk: str = "high"

    def review(self, markdown: str) -> Dict[str, Any]:
        _ = markdown
        return {
            "overall_risk": self.overall_risk,
            "summary": "FakeProvider deterministic review.",
            "findings": [
                {
                    "title": "Test finding",
                    "severity": "high",
                    "description": "A deterministic finding for tests.",
                    "recommendation": "Do the deterministic thing.",
                    "tags": ["test"],
                }
            ],
        }


@pytest.fixture
def fake_provider_high() -> FakeProvider:
    return FakeProvider(overall_risk="high")


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"
