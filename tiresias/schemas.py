from __future__ import annotations

RISK_LEVELS = ["low", "medium", "high", "critical"]
FINDING_SEVERITIES = ["info", "low", "medium", "high", "critical"]


REVIEW_SCHEMA: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "additionalProperties": False,
    "required": ["overall_risk", "summary", "findings"],
    "properties": {
        "overall_risk": {"type": "string", "enum": RISK_LEVELS},
        "blockers": {
            "type": "array",
            "default": [],
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "id",
                    "severity",
                    "status",
                    "title",
                    "pass_criteria",
                ],
                "properties": {
                    "id": {"type": "string", "minLength": 1},
                    "severity": {"type": "string", "enum": FINDING_SEVERITIES},
                    "status": {
                        "type": "string",
                        "enum": ["open", "partial", "resolved", "waived"],
                    },
                    "title": {"type": "string", "minLength": 1},
                    "pass_criteria": {"type": "string", "minLength": 1},
                },
            },
        },
        "summary": {"type": "string", "minLength": 1},
        "findings": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "title",
                    "severity",
                    "description",
                    "recommendation",
                ],
                "properties": {
                    "title": {"type": "string", "minLength": 1},
                    "severity": {"type": "string", "enum": FINDING_SEVERITIES},
                    "description": {"type": "string", "minLength": 1},
                    "recommendation": {"type": "string", "minLength": 1},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    },
}
