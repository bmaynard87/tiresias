from __future__ import annotations

from typing import Any, Dict


class OpenAIProvider:
    """Stub provider (no network).

    V1 returns deterministic placeholder review data.
    """

    def review(self, markdown: str) -> Dict[str, Any]:
        _ = markdown
        return {
            "overall_risk": "high",
            "summary": "Deterministic stub review. Replace with a real provider later.",
            "findings": [
                {
                    "title": "Ambiguous success criteria",
                    "severity": "high",
                    "description": "The document does not define measurable success criteria.",
                    "recommendation": "Add explicit acceptance criteria and measurable KPIs.",
                    "tags": ["clarity", "requirements"],
                }
            ],
        }
